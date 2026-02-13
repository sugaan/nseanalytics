from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select, func, desc
from sqlalchemy.orm import Session, sessionmaker
from pathlib import Path
from loguru import logger
import pandas as pd

from src.models import Base, Announcement, FetchLog
from src.config import config


class Storage:
    def __init__(self, database_path: Optional[str] = None):
        self.database_path = database_path or config.storage.database_path
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f"sqlite:///{self.database_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info(f"Database initialized at {self.database_path}")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def add_announcement(self, announcement_data: dict) -> Optional[Announcement]:
        """Add a new announcement to the database."""
        with self.get_session() as session:
            try:
                # Check if announcement already exists by GUID
                existing = session.execute(
                    select(Announcement).where(Announcement.guid == announcement_data['guid'])
                ).scalar_one_or_none()
                
                if existing:
                    logger.debug(f"Announcement already exists: {announcement_data['guid']}")
                    return None
                
                announcement = Announcement(**announcement_data)
                session.add(announcement)
                session.commit()
                session.refresh(announcement)
                
                logger.info(f"Added announcement: {announcement.symbol} - {announcement.subject[:50]}")
                return announcement
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error adding announcement: {e}")
                raise
    
    def bulk_add_announcements(self, announcements_data: List[dict]) -> tuple[int, int]:
        """Bulk add announcements. Returns (total, new_count)."""
        new_count = 0
        total = len(announcements_data)
        
        with self.get_session() as session:
            for data in announcements_data:
                try:
                    existing = session.execute(
                        select(Announcement).where(Announcement.guid == data['guid'])
                    ).scalar_one_or_none()
                    
                    if not existing:
                        announcement = Announcement(**data)
                        session.add(announcement)
                        new_count += 1
                        
                except Exception as e:
                    logger.error(f"Error in bulk add: {e}")
                    continue
            
            session.commit()
        
        logger.info(f"Bulk add complete: {new_count} new out of {total} total")
        return total, new_count
    
    def get_announcements(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Announcement]:
        """Query announcements with filters."""
        with self.get_session() as session:
            query = select(Announcement)
            
            if symbol:
                query = query.where(Announcement.symbol == symbol.upper())
            if start_date:
                query = query.where(Announcement.broadcast_datetime >= start_date)
            if end_date:
                query = query.where(Announcement.broadcast_datetime <= end_date)
            if category:
                query = query.where(Announcement.category == category)
            
            query = query.order_by(desc(Announcement.broadcast_datetime))
            
            if limit:
                query = query.limit(limit)
            
            result = session.execute(query)
            return list(result.scalars().all())
    
    def get_latest_fetch_time(self, feed_source: str) -> Optional[datetime]:
        """Get the last successful fetch time for a feed."""
        with self.get_session() as session:
            result = session.execute(
                select(FetchLog.fetch_time)
                .where(FetchLog.feed_source == feed_source)
                .where(FetchLog.status == 'success')
                .order_by(desc(FetchLog.fetch_time))
                .limit(1)
            ).scalar_one_or_none()
            
            return result
    
    def log_fetch(self, feed_source: str, status: str, items_fetched: int = 0, 
                  items_new: int = 0, error_message: Optional[str] = None):
        """Log a fetch operation."""
        with self.get_session() as session:
            log_entry = FetchLog(
                feed_source=feed_source,
                status=status,
                items_fetched=items_fetched,
                items_new=items_new,
                error_message=error_message
            )
            session.add(log_entry)
            session.commit()
    
    def get_statistics(self) -> dict:
        """Get database statistics."""
        with self.get_session() as session:
            total_announcements = session.execute(
                select(func.count(Announcement.id))
            ).scalar_one()
            
            unique_symbols = session.execute(
                select(func.count(func.distinct(Announcement.symbol)))
            ).scalar_one()
            
            latest_announcement = session.execute(
                select(Announcement.broadcast_datetime)
                .order_by(desc(Announcement.broadcast_datetime))
                .limit(1)
            ).scalar_one_or_none()
            
            oldest_announcement = session.execute(
                select(Announcement.broadcast_datetime)
                .order_by(Announcement.broadcast_datetime)
                .limit(1)
            ).scalar_one_or_none()
            
            return {
                'total_announcements': total_announcements,
                'unique_symbols': unique_symbols,
                'latest_announcement': latest_announcement,
                'oldest_announcement': oldest_announcement
            }
    
    def export_to_csv(self, output_path: str, **filters):
        """Export announcements to CSV."""
        announcements = self.get_announcements(**filters)
        
        data = [{
            'symbol': a.symbol,
            'company_name': a.company_name,
            'subject': a.subject,
            'description': a.description,
            'broadcast_datetime': a.broadcast_datetime,
            'category': a.category,
            'attachment_url': a.attachment_url,
            'local_attachment_path': a.local_attachment_path,
            'feed_source': a.feed_source
        } for a in announcements]
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(df)} announcements to {output_path}")
        
        return len(df)
