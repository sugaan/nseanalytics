from bse import BSE
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
from pathlib import Path


class BSEApiFetcher:
    def __init__(self, download_folder='./data/attachments'):
        self.download_folder = download_folder
        Path(download_folder).mkdir(parents=True, exist_ok=True)
        
    def fetch_announcements(
        self, 
        page_no: int = 1,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        category: str = '-1',
        segment: str = 'equity'
    ) -> List[Dict]:
        """
        Fetch corporate announcements from BSE.
        
        Args:
            page_no: Page number (default 1)
            from_date: Start date (defaults to today)
            to_date: End date (defaults to today)
            category: Category filter (default '-1' for all)
            segment: 'equity', 'debt', or 'mf_etf'
        """
        announcements = []
        
        with BSE(download_folder=self.download_folder) as bse:
            try:
                # Fetch announcements with correct parameters
                result = bse.announcements(
                    page_no=page_no,
                    from_date=from_date,
                    to_date=to_date,
                    segment=segment,
                    category=category
                )
                
                if not result or 'Table' not in result:
                    logger.warning(f"No announcements data on page {page_no}")
                    return []
                
                # Parse the response
                for item in result.get('Table', []):
                    try:
                        announcement = {
                            'symbol': item.get('SCRIP_CD', 'UNKNOWN'),
                            'company_name': item.get('SLONGNAME', item.get('SMNAME', '')),
                            'subject': item.get('HEADLINE', item.get('NEWS_SUB', '')),
                            'description': item.get('NEWSSUB', item.get('NEWS_BODY', '')),
                            'attachment_url': item.get('ATTACHMENTNAME', item.get('NSURL', '')),
                            'broadcast_datetime': self._parse_bse_datetime(item),
                            'category': item.get('CATEGORYNAME', item.get('CATEGORY', 'General')),
                            'feed_source': 'bse_api',
                            'guid': f"bse_{item.get('NEWSID', '')}_{item.get('SCRIP_CD', '')}",
                            'local_attachment_path': None
                        }
                        announcements.append(announcement)
                        
                    except Exception as e:
                        logger.error(f"Error parsing announcement item: {e}")
                        continue
                
                logger.info(f"Fetched {len(announcements)} announcements from BSE page {page_no}")
                return announcements
                
            except Exception as e:
                logger.error(f"Error fetching BSE announcements page {page_no}: {e}")
                return []
    
    def fetch_all_announcements(
        self,
        max_pages: int = 5,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        category: str = '-1'
    ) -> List[Dict]:
        """Fetch multiple pages of announcements."""
        all_announcements = []
        
        # Default to today if not specified
        if not from_date:
            from_date = datetime.now()
        if not to_date:
            to_date = datetime.now()
        
        for page_no in range(1, max_pages + 1):
            logger.info(f"Fetching BSE announcements page {page_no}")
            announcements = self.fetch_announcements(
                page_no=page_no,
                from_date=from_date,
                to_date=to_date,
                category=category
            )
            
            if not announcements:
                logger.info(f"No more announcements after page {page_no - 1}")
                break
            
            all_announcements.extend(announcements)
        
        logger.info(f"Total BSE announcements fetched: {len(all_announcements)}")
        return all_announcements
    
    def fetch_recent_announcements(self, days: int = 7, max_pages: int = 10) -> List[Dict]:
        """Fetch announcements from the last N days."""
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        logger.info(f"Fetching BSE announcements from {from_date.date()} to {to_date.date()}")
        return self.fetch_all_announcements(
            max_pages=max_pages,
            from_date=from_date,
            to_date=to_date
        )
    
    def fetch_corporate_actions(self, scripcode: str = None) -> List[Dict]:
        """Fetch upcoming corporate actions."""
        with BSE(download_folder=self.download_folder) as bse:
            try:
                # Fetch all actions or for specific scrip
                actions = bse.actions(scripcode=scripcode) if scripcode else bse.actions()
                return self._parse_corporate_actions(actions)
            except Exception as e:
                logger.error(f"Error fetching corporate actions: {e}")
                return []
    
    def _parse_bse_datetime(self, item: dict) -> datetime:
        """Parse BSE date/time from various fields."""
        try:
            # Try different date field names
            date_str = item.get('NEWS_DT') or item.get('DT_TM') or item.get('DISSEM_DT')
            time_str = item.get('NEWSTIME') or item.get('DISSEMINATION_TIME', '')
            
            if date_str:
                # BSE formats: "DD-Mon-YYYY HH:MM:SS" or "DD-Mon-YYYY"
                full_str = f"{date_str} {time_str}".strip()
                
                formats = [
                    "%d-%b-%Y %H:%M:%S",
                    "%d-%b-%Y %I:%M:%S %p",
                    "%d-%b-%Y",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(full_str, fmt)
                    except ValueError:
                        continue
            
            return datetime.now()
        except Exception as e:
            logger.debug(f"Date parse error: {e}")
            return datetime.now()
    
    def _parse_corporate_actions(self, actions_data: dict) -> List[Dict]:
        """Parse corporate actions response."""
        announcements = []
        
        if not actions_data or 'Table' not in actions_data:
            return []
        
        for action in actions_data.get('Table', []):
            try:
                announcement = {
                    'symbol': action.get('SCRIP_CD', ''),
                    'company_name': action.get('SHORT_NAME', action.get('COMPANY', '')),
                    'subject': f"{action.get('CA_TYPE', 'Corporate Action')}: {action.get('PURPOSE', '')}",
                    'description': action.get('PURPOSE', ''),
                    'attachment_url': None,
                    'broadcast_datetime': self._parse_action_date(action.get('EX_DATE', '')),
                    'category': 'Corporate Action',
                    'feed_source': 'bse_api_actions',
                    'guid': f"bse_action_{action.get('SCRIP_CD', '')}_{action.get('EX_DATE', '')}",
                    'local_attachment_path': None
                }
                announcements.append(announcement)
            except Exception as e:
                logger.error(f"Error parsing action: {e}")
                continue
        
        return announcements
    
    def _parse_action_date(self, date_str: str) -> datetime:
        """Parse action date."""
        if not date_str:
            return datetime.now()
        
        formats = ["%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return datetime.now()
