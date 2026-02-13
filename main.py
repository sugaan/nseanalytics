#!/usr/bin/env python3
import sys
from pathlib import Path
from loguru import logger
import argparse

from src.config import config
from src.orchestrator import NSEAnnouncementOrchestrator
from src.scheduler import FetchScheduler


def setup_logging():
    """Configure loguru logging."""
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=config.logging.level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler
    log_path = Path(config.logging.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        config.logging.log_file,
        level=config.logging.level,
        rotation=config.logging.rotation,
        retention=config.logging.retention,
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
    )


def main():
    """Main entry point."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="NSE Announcements RSS Feed Fetcher",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
    '--source',
    choices=['rss', 'bse'],
    default='bse',
    help='Data source (default: bse)'
)

    parser.add_argument(
        '--mode',
        choices=['once', 'schedule', 'stats', 'export', 'query'],
        default='once',
        help='Operation mode (default: once)'
    )
    
    parser.add_argument(
        '--download-attachments',
        action='store_true',
        help='Download PDF attachments'
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        help='Query announcements for specific symbol'
    )
    
    parser.add_argument(
        '--export-path',
        type=str,
        help='Path to export CSV file'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Limit number of results (default: 100)'
    )
    
    args = parser.parse_args()
    
    orchestrator = NSEAnnouncementOrchestrator(source=args.source)
    
    if args.mode == 'once':
        logger.info("Running one-time fetch")
        results = orchestrator.fetch_and_store(download_attachments=args.download_attachments)
        logger.info(f"Results: {results}")
        
    elif args.mode == 'schedule':
        logger.info("Starting scheduler mode")
        scheduler = FetchScheduler()
        scheduler.start()
        
        try:
            # Keep the program running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler")
            scheduler.stop()
    
    elif args.mode == 'stats':
        stats = orchestrator.get_stats()
        logger.info("Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.mode == 'export':
        if not args.export_path:
            logger.error("--export-path is required for export mode")
            sys.exit(1)
        
        count = orchestrator.export_data(
            args.export_path,
            symbol=args.symbol,
            limit=args.limit
        )
        logger.info(f"Exported {count} announcements to {args.export_path}")
    
    elif args.mode == 'query':
        if args.symbol:
            announcements = orchestrator.get_announcements_by_symbol(args.symbol, args.limit)
        else:
            announcements = orchestrator.get_recent_announcements(args.limit)
        
        logger.info(f"Found {len(announcements)} announcements")
        for ann in announcements[:10]:  # Show first 10
            print(f"\n{ann.symbol} - {ann.broadcast_datetime}")
            print(f"  {ann.subject}")


if __name__ == "__main__":
    main()
