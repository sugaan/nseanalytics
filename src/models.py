from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, create_engine, Index, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from pathlib import Path

Base = declarative_base()


class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    subject = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    attachment_url = Column(String(500), nullable=True)
    local_attachment_path = Column(String(500), nullable=True)
    broadcast_datetime = Column(DateTime, nullable=False, index=True)
    category = Column(String(100), nullable=True)
    feed_source = Column(String(100), nullable=False)
    guid = Column(String(500), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symbol_datetime', 'symbol', 'broadcast_datetime'),
        Index('idx_category_datetime', 'category', 'broadcast_datetime'),
    )

    def __repr__(self) -> str:
        return f"<Announcement(symbol={self.symbol}, subject={self.subject[:50]}, date={self.broadcast_datetime})>"


class FetchLog(Base):
    __tablename__ = "fetch_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_source = Column(String(100), nullable=False)
    fetch_time = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), nullable=False)
    items_fetched = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<FetchLog(source={self.feed_source}, time={self.fetch_time}, status={self.status})>"
