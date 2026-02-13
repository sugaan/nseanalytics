from pathlib import Path
from typing import Optional
from loguru import logger
import hashlib
from urllib.parse import urlparse

from src.fetcher import RSSFetcher
from src.config import config


class AttachmentDownloader:
    def __init__(self):
        self.fetcher = RSSFetcher()
        self.attachments_dir = Path(config.storage.attachments_dir)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_filename(self, url: str, symbol: str) -> str:
        """Generate a unique filename for an attachment."""
        # Extract extension from URL
        parsed = urlparse(url)
        path = parsed.path
        extension = Path(path).suffix or '.pdf'
        
        # Create hash of URL for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Create filename: symbol_hash_original.ext
        original_name = Path(path).stem or 'attachment'
        filename = f"{symbol}_{url_hash}_{original_name}{extension}"
        
        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        return filename
    
    def download(self, url: str, symbol: str) -> Optional[str]:
        """Download an attachment and return the local path."""
        try:
            filename = self.generate_filename(url, symbol)
            save_path = self.attachments_dir / filename
            
            # Skip if already downloaded
            if save_path.exists():
                logger.debug(f"Attachment already exists: {filename}")
                return str(save_path)
            
            # Download
            success = self.fetcher.download_attachment(url, str(save_path))
            
            if success:
                return str(save_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error in download process: {e}")
            return None
    
    def download_for_announcement(self, announcement_data: dict) -> Optional[str]:
        """Download attachment for an announcement if available."""
        attachment_url = announcement_data.get('attachment_url')
        
        if not attachment_url:
            return None
        
        symbol = announcement_data.get('symbol', 'UNKNOWN')
        return self.download(attachment_url, symbol)
