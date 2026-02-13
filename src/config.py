from pathlib import Path
from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings
import yaml


class RSSFeedsConfig(BaseSettings):
    announcements: str
    financial_results: str
    board_meetings: str


class StorageConfig(BaseSettings):
    database_path: str = "data/announcements.db"
    attachments_dir: str = "data/attachments"


class FetcherConfig(BaseSettings):
    user_agent: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5


class SchedulerConfig(BaseSettings):
    enabled: bool = True
    interval_minutes: int = 30


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    log_file: str = "logs/app.log"
    rotation: str = "1 day"
    retention: str = "30 days"


class Config(BaseSettings):
    rss_feeds: RSSFeedsConfig
    storage: StorageConfig
    fetcher: FetcherConfig
    scheduler: SchedulerConfig
    logging: LoggingConfig

    @classmethod
    def load_from_yaml(cls, config_path: str = "config/config.yaml") -> "Config":
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)


# Global config instance
config = Config.load_from_yaml()
