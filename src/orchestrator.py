from typing import Dict, List
from loguru import logger

from src.fetcher import RSSFetcher
from src.parser import AnnouncementParser
from src.storage import Storage
from src.downloader import AttachmentDownloader
from src.fetcher_bse import BSEApiFetcher


class NSEAnnouncementOrchestrator:
    def __init__(self, source='rss'):
        self.source = source
        
        if source == 'bse':
            self.bse_fetcher = BSEApiFetcher()
        else:
            self.fetcher = RSSFetcher()
            self.parser = AnnouncementParser()
        
        self.storage = Storage()
        self.downloader = AttachmentDownloader()
    
    def fetch_and_store(self, download_attachments: bool = False) -> Dict[str, int]:
        """Main orchestration method to fetch, parse, and store announcements."""
        logger.info(f"Starting fetch from {self.source}")
        
        if self.source == 'bse':
            return self._fetch_from_bse(download_attachments)
        else:
            return self._fetch_from_rss(download_attachments)
    
    def _fetch_from_bse(self, download_attachments: bool) -> Dict[str, int]:
        """Fetch from BSE API."""
        announcements = self.bse_fetcher.fetch_all_announcements(max_pages=5)
        
        if download_attachments:
            for announcement in announcements:
                if announcement.get('attachment_url'):
                    local_path = self.downloader.download_for_announcement(announcement)
                    announcement['local_attachment_path'] = local_path
        
        total, new_count = self.storage.bulk_add_announcements(announcements)
        
        self.storage.log_fetch(
            feed_source='bse_announcements',
            status='success',
            items_fetched=total,
            items_new=new_count
        )
        
        return {
            'total_fetched': total,
            'total_new': new_count,
            'feeds_processed': 1,
            'feeds_failed': 0
        }
    
    def _fetch_from_rss(self, download_attachments: bool) -> Dict[str, int]:
        """Fetch from RSS feeds."""
        logger.info("Starting fetch and store operation")
        
        # Fetch all feeds
        feeds = self.fetcher.fetch_all_feeds()
        
        results = {
            'total_fetched': 0,
            'total_new': 0,
            'feeds_processed': 0,
            'feeds_failed': 0
        }
        
        for feed_name, feed in feeds.items():
            if not feed:
                results['feeds_failed'] += 1
                self.storage.log_fetch(feed_name, 'error', error_message='Failed to fetch feed')
                continue
            
            try:
                # Parse feed entries
                announcements = self.parser.parse_feed(feed, feed_name)
                results['total_fetched'] += len(announcements)
                
                # Download attachments if requested
                if download_attachments:
                    for announcement in announcements:
                        if announcement.get('attachment_url'):
                            local_path = self.downloader.download_for_announcement(announcement)
                            announcement['local_attachment_path'] = local_path
                
                # Store in database
                total, new_count = self.storage.bulk_add_announcements(announcements)
                results['total_new'] += new_count
                results['feeds_processed'] += 1
                
                # Log the fetch operation
                self.storage.log_fetch(
                    feed_source=feed_name,
                    status='success',
                    items_fetched=total,
                    items_new=new_count
                )
                
            except Exception as e:
                logger.error(f"Error processing feed {feed_name}: {e}")
                results['feeds_failed'] += 1
                self.storage.log_fetch(
                    feed_source=feed_name,
                    status='error',
                    error_message=str(e)
                )
        
        logger.info(f"Fetch complete: {results}")
        return results
    
    def get_announcements_by_symbol(self, symbol: str, limit: int = 50):
        """Get announcements for a specific symbol."""
        return self.storage.get_announcements(symbol=symbol, limit=limit)
    
    def get_recent_announcements(self, limit: int = 100):
        """Get most recent announcements."""
        return self.storage.get_announcements(limit=limit)
    
    def export_data(self, output_path: str, **filters):
        """Export announcements to CSV."""
        return self.storage.export_to_csv(output_path, **filters)
    
    def get_stats(self):
        """Get database statistics."""
        return self.storage.get_statistics()
