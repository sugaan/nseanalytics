"""Scraper wrapper for BSE announcements"""
from src.fetcher_bse import BSEApiFetcher

class BSEScraper:
    """Wrapper class for BSE scraping"""
    
    def __init__(self):
        self.fetcher = BSEApiFetcher()
    
    def fetch_announcements(self):
        """Fetch announcements using BSEApiFetcher"""
        try:
            return self.fetcher.fetch_announcements()
        except Exception as e:
            print(f"Error fetching announcements: {e}")
            return []
