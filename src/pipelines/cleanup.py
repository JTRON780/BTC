"""
Database cleanup pipeline for data retention policy.

Removes raw_items and scored_items older than a specified retention period
while preserving sentiment_indices for historical charting.

Usage:
    python -m src.pipelines.cleanup --retention-days 60
"""

import argparse
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.core import get_logger, get_settings
from src.data import init_db, get_engine, RawItem, ScoredItem


logger = get_logger(__name__)


def cleanup_old_data(retention_days: int = 60) -> Dict[str, Any]:
    """
    Remove raw_items and scored_items older than retention period.
    
    Sentiment indices are preserved for historical charting regardless of age.
    
    Args:
        retention_days: Number of days to keep raw/scored data (default: 60)
        
    Returns:
        Dictionary with cleanup statistics
    """
    config = get_settings()
    init_db(config.DB_URL)
    engine = get_engine()
    
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    logger.info(
        "Starting data cleanup",
        extra={"retention_days": retention_days, "cutoff_date": cutoff_date.isoformat()}
    )
    
    stats = {
        "raw_items_deleted": 0,
        "scored_items_deleted": 0,
        "cutoff_date": cutoff_date.isoformat(),
        "retention_days": retention_days
    }
    
    with Session(engine) as session:
        # Delete old raw items
        raw_delete_stmt = delete(RawItem).where(RawItem.ts < cutoff_date)
        raw_result = session.execute(raw_delete_stmt)
        stats["raw_items_deleted"] = raw_result.rowcount
        
        # Delete old scored items
        scored_delete_stmt = delete(ScoredItem).where(ScoredItem.ts < cutoff_date)
        scored_result = session.execute(scored_delete_stmt)
        stats["scored_items_deleted"] = scored_result.rowcount
        
        session.commit()
    
    logger.info(
        "Cleanup complete",
        extra=stats
    )
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old data while preserving aggregated indices"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=60,
        help="Number of days to retain raw/scored data (default: 60)"
    )
    
    args = parser.parse_args()
    
    print("🧹 Database Cleanup Pipeline")
    print("=" * 60)
    print(f"Retention period: {args.retention_days} days")
    print(f"Note: Sentiment indices are preserved indefinitely")
    print()
    
    stats = cleanup_old_data(retention_days=args.retention_days)
    
    print("\n📊 Cleanup Results:")
    print("-" * 60)
    print(f"Cutoff date:         {stats['cutoff_date']}")
    print(f"Raw items deleted:   {stats['raw_items_deleted']}")
    print(f"Scored items deleted: {stats['scored_items_deleted']}")
    print()
    print("✅ Sentiment indices preserved for historical charts")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
