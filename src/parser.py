from typing import Dict, List, Optional
from datetime import datetime
import re
from loguru import logger
from bs4 import BeautifulSoup
import feedparser


class AnnouncementParser:
    def __init__(self):
        pass
    
    @staticmethod
    def parse_datetime(date_str: str) -> Optional[datetime]:
        """Parse various date formats from RSS feeds."""
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d-%b-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try feedparser's built-in parsing
        try:
            time_tuple = feedparser._parse_date(date_str)
            if time_tuple:
                return datetime(*time_tuple[:6])
        except:
            pass
        
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.utcnow()
    
    @staticmethod
    def extract_symbol(text: str) -> Optional[str]:
        """Extract stock symbol from text."""
        # Common patterns: "SYMBOL:" or "(SYMBOL)" or just uppercase word
        patterns = [
            r'Symbol:\s*([A-Z0-9]+)',
            r'\(([A-Z0-9]+)\)',
            r'\b([A-Z]{2,})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def clean_html(html_text: str) -> str:
        """Remove HTML tags and clean text."""
        if not html_text:
            return ""
        
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text
    
    @staticmethod
    def extract_attachment_url(entry: feedparser.FeedParserDict) -> Optional[str]:
        """Extract attachment URL from feed entry."""
        # Check for enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            return entry.enclosures[0].get('href') or entry.enclosures[0].get('url')
        
        # Check for links with rel="enclosure"
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('rel') == 'enclosure' or link.get('type', '').startswith('application/'):
                    return link.get('href')
        
        # Look for PDF links in content
        content = entry.get('summary', '') + entry.get('description', '')
        pdf_match = re.search(r'https?://[^\s]+\.pdf', content, re.IGNORECASE)
        if pdf_match:
            return pdf_match.group(0)
        
        return None
    
    def parse_entry(self, entry: feedparser.FeedParserDict, feed_source: str) -> Dict:
        """Parse a single RSS feed entry into announcement data."""
        # Extract basic fields
        title = entry.get('title', '').strip()
        description = self.clean_html(entry.get('description', '') or entry.get('summary', ''))
        
        # Extract symbol and company name
        symbol = self.extract_symbol(title) or self.extract_symbol(description) or "UNKNOWN"
        company_name = title.split('-')[0].strip() if '-' in title else title[:100]
        
        # Parse date
        published_date = entry.get('published', '') or entry.get('updated', '')
        broadcast_datetime = self.parse_datetime(published_date) if published_date else datetime.utcnow()
        
        # Extract attachment
        attachment_url = self.extract_attachment_url(entry)
        
        # Create GUID
        guid = entry.get('id') or entry.get('link') or f"{symbol}_{broadcast_datetime.isoformat()}"
        
        # Determine category
        category = self._determine_category(title, description, feed_source)
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'subject': title,
            'description': description,
            'attachment_url': attachment_url,
            'broadcast_datetime': broadcast_datetime,
            'category': category,
            'feed_source': feed_source,
            'guid': guid,
            'local_attachment_path': None
        }
    
    def _determine_category(self, title: str, description: str, feed_source: str) -> str:
        """Determine the category based on content."""
        text = (title + " " + description).lower()
        
        if feed_source == 'financial_results':
            return 'Financial Results'
        elif feed_source == 'board_meetings':
            return 'Board Meeting'
        
        # Category detection for announcements
        if any(word in text for word in ['dividend', 'bonus', 'split']):
            return 'Corporate Action'
        elif any(word in text for word in ['agm', 'egm', 'annual general meeting']):
            return 'Meeting Notice'
        elif any(word in text for word in ['result', 'financial', 'quarter', 'fy']):
            return 'Financial Results'
        elif any(word in text for word in ['acquisition', 'merger', 'buyback']):
            return 'Major Event'
        else:
            return 'General Announcement'
    
    def parse_feed(self, feed: feedparser.FeedParserDict, feed_source: str) -> List[Dict]:
        """Parse all entries in a feed."""
        if not feed or not hasattr(feed, 'entries'):
            return []
        
        announcements = []
        for entry in feed.entries:
            try:
                announcement = self.parse_entry(entry, feed_source)
                announcements.append(announcement)
            except Exception as e:
                logger.error(f"Error parsing entry: {e}")
                continue
        
        logger.info(f"Parsed {len(announcements)} announcements from {feed_source}")
        return announcements
