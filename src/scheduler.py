from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from datetime import datetime

from src.orchestrator import NSEAnnouncementOrchestrator
from src.config import config


class FetchScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.orchestrator = NSEAnnouncementOrchestrator()
    
    def scheduled_fetch(self):
        """The job that runs on schedule."""
        logger.info(f"Scheduled fetch started at {datetime.now()}")
        try:
            results = self.orchestrator.fetch_and_store(download_attachments=False)
            logger.info(f"Scheduled fetch completed: {results}")
        except Exception as e:
            logger.error(f"Error in scheduled fetch: {e}")
    
    def start(self):
        """Start the scheduler."""
        if not config.scheduler.enabled:
            logger.info("Scheduler is disabled in config")
            return
        
        interval_minutes = config.scheduler.interval_minutes
        
        self.scheduler.add_job(
            self.scheduled_fetch,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='nse_fetch_job',
            name='Fetch NSE Announcements',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started with {interval_minutes} minute interval")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def run_now(self):
        """Manually trigger a fetch."""
        logger.info("Manual fetch triggered")
        self.scheduled_fetch()
