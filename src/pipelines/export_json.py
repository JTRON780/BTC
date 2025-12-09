"""
Export database data to static JSON files for GitHub Pages API.

This script exports sentiment indices, price data, and top drivers to JSON files
that can be served statically via GitHub Pages, eliminating the need for a backend server.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from src.core import get_logger, get_settings
from src.data import get_engine, init_db
from src.ingest.price import fetch_current_price
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session
from src.data.schemas import SentimentIndex, ScoredItem, RawItem

logger = get_logger(__name__)


def export_sentiment_indices(
    output_dir: str | Path,
    granularity: str = "daily",
    days: int = 30
) -> None:
    """
    Export sentiment indices to JSON file.
    
    Args:
        output_dir: Directory to write JSON files
        granularity: Either 'daily' or 'hourly'
        days: Number of days to export
    """
    output_dir = Path(output_dir)
    logger.info(f"Exporting {granularity} sentiment indices for {days} days")
    
    engine = get_engine()
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    with Session(engine) as session:
        stmt = (
            select(SentimentIndex)
            .where(
                and_(
                    SentimentIndex.granularity == granularity,
                    SentimentIndex.ts >= cutoff_time
                )
            )
            .order_by(SentimentIndex.ts.asc())
        )
        
        results = session.execute(stmt).scalars().all()
        
        data = {
            "granularity": granularity,
            "data": [
                {
                    "ts": item.ts.isoformat(),
                    "raw": item.raw_value,
                    "smoothed": item.smoothed_value if item.smoothed_value is not None else item.raw_value,
                    "n_posts": item.n_posts
                }
                for item in results
            ]
        }
    
    # Write to file
    output_file = output_dir / f"sentiment_{granularity}.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Exported {len(data['data'])} records to {output_file}")


def export_top_drivers(output_dir: str | Path, days: int = 7) -> None:
    """
    Export top sentiment drivers (positive and negative posts) for each day.
    
    Args:
        output_dir: Directory to write JSON files
        days: Number of days to export
    """
    output_dir = Path(output_dir)
    logger.info(f"Exporting top drivers for {days} days")
    
    engine = get_engine()
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    with Session(engine) as session:
        # Get all scored items from the last N days, joined with raw items
        stmt = (
            select(ScoredItem, RawItem)
            .join(RawItem, ScoredItem.id == RawItem.id)
            .where(ScoredItem.ts >= cutoff_time)
            .order_by(desc(ScoredItem.polarity))
        )
        
        results = session.execute(stmt).all()
        
        # Group by day
        drivers_by_day: Dict[str, Dict[str, List[Dict]]] = {}
        
        for scored_item, raw_item in results:
            day = scored_item.ts.strftime('%Y-%m-%d')
            
            if day not in drivers_by_day:
                drivers_by_day[day] = {"positives": [], "negatives": []}
            
            item_data = {
                "title": raw_item.title or scored_item.id,  # Use actual title
                "polarity": scored_item.polarity,
                "ts": scored_item.ts.isoformat(),
                "source": scored_item.source,
                "url": raw_item.url or ""  # Add URL
            }
            
            # Add to appropriate list
            # Type ignore: polarity is a float on the Python object, not SQLAlchemy column
            if scored_item.polarity > 0 and len(drivers_by_day[day]["positives"]) < 10:  # type: ignore
                drivers_by_day[day]["positives"].append(item_data)
            elif scored_item.polarity < 0 and len(drivers_by_day[day]["negatives"]) < 10:  # type: ignore
                drivers_by_day[day]["negatives"].append(item_data)
    
    # Sort negatives by most negative first
    for day in drivers_by_day:
        drivers_by_day[day]["negatives"].sort(key=lambda x: x["polarity"])
    
    # Write each day to a separate file
    drivers_dir = output_dir / "drivers"
    drivers_dir.mkdir(exist_ok=True)
    
    for day, data in drivers_by_day.items():
        output_file = drivers_dir / f"{day}.json"
        with open(output_file, 'w') as f:
            json.dump({"day": day, **data}, f, indent=2)
        
        logger.info(f"Exported drivers for {day}: {len(data['positives'])} positive, {len(data['negatives'])} negative")


def export_current_price(output_dir: str | Path) -> None:
    """
    Export current Bitcoin price data.
    
    Args:
        output_dir: Directory to write JSON files
    """
    output_dir = Path(output_dir)
    logger.info("Exporting current Bitcoin price")
    
    try:
        price_data = fetch_current_price()
        
        data = {
            "price": price_data['price'],
            "price_change_24h": price_data['price_change_24h'],
            "volume_24h": price_data['volume_24h'],
            "last_updated": price_data['last_updated'].isoformat()
        }
        
        output_file = output_dir / "price.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported price data: ${data['price']:,.2f} ({data['price_change_24h']:+.2f}%)")
    
    except Exception as e:
        logger.error(f"Failed to export price data: {e}")
        # Create empty price file as fallback
        output_file = output_dir / "price.json"
        with open(output_file, 'w') as f:
            json.dump({"error": "Failed to fetch price data"}, f, indent=2)


def run_export(output_dir: str = "api-output") -> None:
    """
    Run full JSON export for GitHub Pages deployment.
    
    Args:
        output_dir: Directory to write all JSON files
    """
    config = get_settings()
    init_db(config.DB_URL)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    logger.info(f"Starting JSON export to {output_path}")
    
    # Export sentiment indices
    export_sentiment_indices(output_path, granularity="daily", days=30)
    export_sentiment_indices(output_path, granularity="hourly", days=7)
    
    # Export top drivers
    export_top_drivers(output_path, days=7)
    
    # Export current price
    export_current_price(output_path)
    
    logger.info("JSON export complete!")
    
    # Create index file
    index_data = {
        "api": "BTC Sentiment Analysis Static API",
        "version": "1.0",
        "updated": datetime.utcnow().isoformat(),
        "endpoints": {
            "sentiment_daily": "/sentiment_daily.json",
            "sentiment_hourly": "/sentiment_hourly.json",
            "price": "/price.json",
            "drivers": "/drivers/{date}.json"
        }
    }
    
    with open(output_path / "index.json", 'w') as f:
        json.dump(index_data, f, indent=2)


if __name__ == "__main__":
    import sys
    
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "api-output"
    
    print("=" * 60)
    print("BTC Sentiment - JSON Export")
    print("=" * 60)
    print()
    
    run_export(output_dir)
    
    print()
    print("=" * 60)
    print("✅ Export complete!")
    print("=" * 60)
