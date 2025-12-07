"""
Automated pipeline scheduler.

This module provides a scheduler that runs the data collection, scoring,
and aggregation pipelines on a regular schedule.

Usage:
    # Run scheduler (runs pipelines every hour)
    python -m src.pipelines.scheduler
    
    # Or use as a service
    python -m src.pipelines.scheduler --daemon
"""

import argparse
import time
import signal
import sys
from datetime import datetime
from typing import Optional

from src.core import get_logger, get_settings
from src.pipelines.collect import run_collect
from src.pipelines.score import run_scoring_pipeline
from src.pipelines.aggregate import run_aggregation

logger = get_logger(__name__)

# Global flag for graceful shutdown
_shutdown = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown
    logger.info("Received shutdown signal, stopping scheduler...")
    _shutdown = True


def run_full_pipeline() -> dict:
    """
    Run the complete pipeline: collect -> score -> aggregate.
    
    Returns:
        Dictionary with pipeline statistics
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Starting full pipeline run")
    logger.info("=" * 60)
    
    stats = {
        'collection': {},
        'scoring': {},
        'aggregation_hourly': {},
        'aggregation_daily': {},
        'total_time': 0,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        # Step 1: Collect data
        logger.info("Step 1: Collecting data...")
        collection_stats = run_collect()
        stats['collection'] = collection_stats
        logger.info(f"Collection complete: {collection_stats}")
        
        # Step 2: Score sentiment
        logger.info("Step 2: Scoring sentiment...")
        scoring_stats = run_scoring_pipeline(since_hours=24)
        stats['scoring'] = scoring_stats
        logger.info(f"Scoring complete: {scoring_stats}")
        
        # Step 3: Aggregate hourly indices
        logger.info("Step 3: Aggregating hourly indices...")
        hourly_stats = run_aggregation(granularity='hourly', days=7)
        stats['aggregation_hourly'] = hourly_stats
        logger.info(f"Hourly aggregation complete: {hourly_stats}")
        
        # Step 4: Aggregate daily indices
        logger.info("Step 4: Aggregating daily indices...")
        daily_stats = run_aggregation(granularity='daily', days=30)
        stats['aggregation_daily'] = daily_stats
        logger.info(f"Daily aggregation complete: {daily_stats}")
        
        total_time = time.time() - start_time
        stats['total_time'] = total_time
        
        logger.info("=" * 60)
        logger.info(f"Full pipeline complete in {total_time:.2f}s")
        logger.info("=" * 60)
        
        return stats
        
    except Exception as e:
        logger.error(f"Pipeline failed", extra={'error': str(e)})
        stats['error'] = str(e)
        return stats


def run_scheduler(interval_hours: int = 1, daemon: bool = False):
    """
    Run the scheduler that executes pipelines at regular intervals.
    
    Args:
        interval_hours: Hours between pipeline runs (default: 1)
        daemon: Run as daemon (continuous loop) or single run
    """
    global _shutdown
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("BTC Sentiment Pipeline Scheduler")
    logger.info("=" * 60)
    logger.info(f"Interval: {interval_hours} hour(s)")
    logger.info(f"Mode: {'Daemon' if daemon else 'Single run'}")
    logger.info("=" * 60)
    
    if not daemon:
        # Single run mode
        logger.info("Running single pipeline execution...")
        stats = run_full_pipeline()
        
        # Print summary
        print("\n" + "=" * 60)
        print("Pipeline Summary")
        print("=" * 60)
        print(f"Collection:     {stats['collection']}")
        print(f"Scoring:        {stats['scoring']}")
        print(f"Hourly Agg:     {stats['aggregation_hourly']}")
        print(f"Daily Agg:      {stats['aggregation_daily']}")
        print(f"Total Time:     {stats['total_time']:.2f}s")
        print("=" * 60)
        
        return
    
    # Daemon mode - continuous loop
    interval_seconds = interval_hours * 3600
    next_run = time.time()
    
    logger.info(f"Starting daemon mode. Next run in {interval_hours} hour(s)")
    logger.info("Press Ctrl+C to stop")
    
    while not _shutdown:
        current_time = time.time()
        
        if current_time >= next_run:
            logger.info(f"Scheduled run at {datetime.utcnow().isoformat()}")
            stats = run_full_pipeline()
            
            # Calculate next run time
            next_run = current_time + interval_seconds
            logger.info(f"Next run scheduled for {datetime.fromtimestamp(next_run).isoformat()}")
        
        # Sleep for 60 seconds, then check again
        time.sleep(60)
    
    logger.info("Scheduler stopped")


def main():
    """CLI entry point for the scheduler."""
    parser = argparse.ArgumentParser(
        description='Automated pipeline scheduler for BTC sentiment analysis'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=1,
        help='Hours between pipeline runs (default: 1)'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon (continuous loop) instead of single run'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run pipeline once and exit (default behavior)'
    )
    
    args = parser.parse_args()
    
    # If --once is specified or --daemon is not, run once
    daemon_mode = args.daemon and not args.once
    
    run_scheduler(interval_hours=args.interval, daemon=daemon_mode)


if __name__ == "__main__":
    main()

