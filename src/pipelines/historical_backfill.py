"""
Historical data backfill for populating past 30 days of sentiment data.

This module generates synthetic historical data points based on recent patterns
to populate the database for demonstration and testing. In production, this would
fetch real historical data from APIs or archives.

Usage:
    python -m src.pipelines.historical_backfill --days 30
"""

import argparse
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import hashlib

from src.core import get_logger, get_settings
from src.data import init_db, upsert_raw_items, save_prices
from src.ingest.price import backfill_prices


logger = get_logger(__name__)


def generate_historical_bitcoin_items(days: int = 30) -> List[Dict[str, Any]]:
    """
    Generate historical Bitcoin-related content items.
    
    In production, this would fetch real historical data from:
    - News API archives
    - Reddit API (with proper credentials)
    - Web archives
    
    For now, generates representative items with realistic timestamps.
    """
    items = []
    
    # Common Bitcoin news patterns
    news_templates = [
        "Bitcoin {action} to ${price} as {reason}",
        "Analysts {sentiment} on Bitcoin's {timeframe} outlook",
        "Bitcoin network {metric} reaches {milestone}",
        "Major {entity} {action} Bitcoin holdings",
        "Bitcoin {indicator} signals potential {direction} move",
    ]
    
    actions = ["climbs", "rises", "dips", "falls", "rallies", "holds steady"]
    reasons = [
        "institutional adoption increases",
        "market sentiment shifts",
        "regulatory clarity emerges",
        "on-chain metrics improve",
        "macroeconomic data released",
        "major exchange updates announced"
    ]
    sentiments = ["bullish", "cautious", "optimistic", "mixed", "positive"]
    timeframes = ["short-term", "medium-term", "long-term", "Q4", "2026"]
    metrics = ["hash rate", "transaction volume", "active addresses", "difficulty"]
    milestones = ["all-time high", "new record", "significant level"]
    entities = ["institution", "fund", "company", "exchange", "whale"]
    indicators = ["RSI", "MVRV", "funding rate", "open interest"]
    directions = ["bullish", "bearish", "upward", "consolidation"]
    
    base_price = 90000
    
    for day_offset in range(days, 0, -1):
        # Create 2-5 items per day
        items_per_day = random.randint(2, 5)
        
        for item_num in range(items_per_day):
            # Spread throughout the day
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            ts = datetime.utcnow() - timedelta(days=day_offset, hours=hour, minutes=minute)
            
            # Generate content
            template = random.choice(news_templates)
            price = base_price + random.randint(-10000, 10000)
            
            title = template.format(
                action=random.choice(actions),
                price=f"{price:,}",
                reason=random.choice(reasons),
                sentiment=random.choice(sentiments),
                timeframe=random.choice(timeframes),
                metric=random.choice(metrics),
                milestone=random.choice(milestones),
                entity=random.choice(entities),
                indicator=random.choice(indicators),
                direction=random.choice(directions)
            )
            
            # Generate text with Bitcoin context
            text_parts = [
                f"Bitcoin (BTC) continues to show {random.choice(['strength', 'volatility', 'resilience', 'momentum'])} in the current market environment.",
                f"Recent {random.choice(['on-chain', 'technical', 'fundamental'])} analysis suggests {random.choice(['continued growth', 'consolidation', 'increased activity'])}.",
                f"Market participants remain {random.choice(['optimistic', 'cautious', 'engaged', 'active'])} as Bitcoin {random.choice(['develops', 'matures', 'evolves'])}."
            ]
            text = " ".join(random.sample(text_parts, 2))
            
            # Create unique ID
            unique_str = f"{ts.isoformat()}{title}{item_num}"
            item_id = f"backfill_{hashlib.sha256(unique_str.encode()).hexdigest()[:16]}"
            
            item = {
                'id': item_id,
                'source': random.choice(['news', 'news']),  # More news
                'ts': ts,
                'title': title,
                'text': text,
                'url': f'https://example.com/backfill/{item_id}'
            }
            
            items.append(item)
    
    logger.info(f"Generated {len(items)} historical items for {days} days")
    return items


def run_historical_backfill(days: int = 30) -> Dict[str, Any]:
    """
    Run historical backfill for the specified number of days.
    
    Steps:
    1. Generate/fetch historical content items
    2. Backfill price data
    3. Save items to database
    4. Score items (call score pipeline)
    5. Aggregate indices (call aggregate pipeline)
    """
    config = get_settings()
    init_db(config.DB_URL)
    
    logger.info(f"Starting historical backfill for {days} days")
    
    stats = {
        'days': days,
        'items_generated': 0,
        'items_saved': 0,
        'prices_saved': 0
    }
    
    # Step 1: Generate historical items
    print(f"📚 Generating historical Bitcoin content for {days} days...")
    items = generate_historical_bitcoin_items(days=days)
    stats['items_generated'] = len(items)
    
    # Step 2: Save items
    print(f"💾 Saving {len(items)} historical items to database...")
    saved_count = upsert_raw_items(items)
    stats['items_saved'] = saved_count
    
    # Step 3: Backfill price data
    print(f"💰 Backfilling price data for {days} days...")
    hours = days * 24
    try:
        prices = backfill_prices(hours=hours)
        from src.data import save_prices
        price_count = save_prices(prices) if prices else 0
        stats['prices_saved'] = price_count
        print(f"✅ Saved {price_count} price points")
    except Exception as e:
        logger.warning(f"Price backfill failed: {e}")
        print(f"⚠️ Price backfill failed (not critical): {e}")
        stats['prices_saved'] = 0
    
    logger.info("Historical backfill complete", extra=stats)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Backfill historical Bitcoin sentiment data"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to backfill (default: 30)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📜 Historical Bitcoin Sentiment Backfill")
    print("=" * 70)
    print(f"Backfilling: {args.days} days")
    print()
    
    stats = run_historical_backfill(days=args.days)
    
    print()
    print("=" * 70)
    print("📊 Backfill Results:")
    print("-" * 70)
    print(f"Days backfilled:     {stats['days']}")
    print(f"Items generated:     {stats['items_generated']}")
    print(f"Items saved:         {stats['items_saved']}")
    print(f"Price points saved:  {stats['prices_saved']}")
    print()
    print("✅ Historical data backfill complete!")
    print()
    print("Next steps:")
    print("  1. Run scoring:     python -m src.pipelines.score --since-hours 720")
    print("  2. Run aggregation: python -m src.pipelines.aggregate --granularity daily --days 30")
    print("  3. Run aggregation: python -m src.pipelines.aggregate --granularity hourly --days 7")
    print("=" * 70)


if __name__ == "__main__":
    main()
