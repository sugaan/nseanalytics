import feedparser
import requests
from typing import Dict, List, Optional
from datetime import datetime
from time import sleep
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import config


class RSSFetcher:
    def __init__(self):
        self.session = self._create_session()
        self.headers = {
            'User-Agent': config.fetcher.user_agent,
            'Accept': 'application/rss+xml, application/xml, text/xml',
        }
    
    def _create_session(self) -> requests.Session:
        """Create a session with retry logic."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=config.fetcher.max_retries,
            backoff_factor=config.fetcher.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def fetch_feed(self, feed_url: str, feed_name: str) -> Optional[feedparser.FeedParserDict]:
        """Fetch and parse an RSS feed."""
        try:
            logger.info(f"Fetching feed: {feed_name} from {feed_url}")
            
            response = self.session.get(
                feed_url,
                headers=self.headers,
                timeout=config.fetcher.timeout
            )
            response.raise_for_status()
            
            # Parse the feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:  # bozo bit indicates feed parsing errors
                logger.warning(f"Feed parsing warning for {feed_name}: {feed.bozo_exception}")
            
            logger.info(f"Successfully fetched {len(feed.entries)} entries from {feed_name}")
            return feed
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching feed {feed_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing feed {feed_name}: {e}")
            return None
    
    def fetch_all_feeds(self) -> Dict[str, Optional[feedparser.FeedParserDict]]:
        """Fetch all configured RSS feeds."""
        feeds = {}
        feed_configs = {
            'announcements': config.rss_feeds.announcements,
            'financial_results': config.rss_feeds.financial_results,
            'board_meetings': config.rss_feeds.board_meetings
        }
        
        for feed_name, feed_url in feed_configs.items():
            feed = self.fetch_feed(feed_url, feed_name)
            feeds[feed_name] = feed
            
            # Be respectful - add delay between requests
            sleep(1)
        
        return feeds
    
    def download_attachment(self, url: str, save_path: str) -> bool:
        """Download an attachment from URL."""
        try:
            response = self.session.get(url, timeout=config.fetcher.timeout, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded attachment to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading attachment from {url}: {e}")
            return False
