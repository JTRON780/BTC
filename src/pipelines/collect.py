"""
Unified data collection pipeline.

This script fetches raw content from configured sources (news RSS and Reddit),
captures a current BTC price snapshot, and persists them into the database.

Usage:
	python -m src.pipelines.collect

CLI Options:
	--skip-news      Skip collecting news feeds
	--skip-reddit    Skip collecting Reddit feeds
	--skip-price     Skip capturing price snapshot

Environment:
	Reads configuration from `.env` via `src.core.get_settings()`.
"""

import argparse
from typing import Dict, Any, List

from src.core import get_logger, get_settings
from src.data import init_db, upsert_raw_items, save_prices
from src.ingest.news import fetch_news_feeds
from src.ingest.reddit import fetch_reddit_feeds
from src.ingest.price import fetch_price_snapshot


logger = get_logger(__name__)

# Bitcoin-related keywords for filtering
BTC_KEYWORDS = [
    'bitcoin', 'btc', 'satoshi', 'sats', 'nakamoto',
    'lightning network', 'taproot', 'ordinals'
]


def is_bitcoin_related(item: Dict[str, Any]) -> bool:
    """Check if an item is Bitcoin-related based on title and text."""
    title = item.get('title', '').lower()
    text = item.get('text', '').lower()
    combined = f"{title} {text}"
    
    return any(keyword in combined for keyword in BTC_KEYWORDS)


def collect_news(feeds: List[str]) -> int:
    """Fetch and persist Bitcoin-related news items."""
    items = fetch_news_feeds(feeds)
    if not items:
        logger.info("No news items fetched")
        return 0
    
    # Filter to Bitcoin-related items only
    btc_items = [item for item in items if is_bitcoin_related(item)]
    filtered_count = len(items) - len(btc_items)
    
    if filtered_count > 0:
        logger.info(
            "Filtered non-Bitcoin items",
            extra={"total": len(items), "filtered": filtered_count, "kept": len(btc_items)}
        )
    
    if not btc_items:
        logger.info("No Bitcoin-related news items found")
        return 0
    
    count = upsert_raw_items(btc_items)
    logger.info("Bitcoin news items saved", extra={"count": count})
    return count
def collect_reddit(feeds: List[str]) -> int:
    """Fetch and persist Bitcoin-related reddit items."""
    items = fetch_reddit_feeds(feeds)
    if not items:
        logger.info("No reddit items fetched")
        return 0
    
    # Filter to Bitcoin-related items only
    btc_items = [item for item in items if is_bitcoin_related(item)]
    filtered_count = len(items) - len(btc_items)
    
    if filtered_count > 0:
        logger.info(
            "Filtered non-Bitcoin items",
            extra={"total": len(items), "filtered": filtered_count, "kept": len(btc_items)}
        )
    
    if not btc_items:
        logger.info("No Bitcoin-related reddit items found")
        return 0
    
    count = upsert_raw_items(btc_items)
    logger.info("Bitcoin reddit items saved", extra={"count": count})
    return count
def collect_price_snapshot() -> int:
	"""Fetch and persist a single BTC price snapshot."""
	try:
		snapshot = fetch_price_snapshot()
		save_prices([snapshot])
		logger.info(
			"Price snapshot saved",
			extra={"price": snapshot["price"], "volume": snapshot["volume"]},
		)
		return 1
	except Exception as e:
		logger.error("Failed to fetch/save price snapshot", extra={"error": str(e)})
		return 0


def run_collect(skip_news: bool = False, skip_reddit: bool = False, skip_price: bool = False) -> Dict[str, Any]:
	"""
	Run the collection pipeline once.

	Returns stats dict with counts for each source.
	"""
	config = get_settings()
	init_db(config.DB_URL)

	stats = {"news": 0, "reddit": 0, "price_snapshots": 0}

	# Normalize feed configs to lists
	news_feeds: List[str] = config.NEWS_FEEDS if isinstance(config.NEWS_FEEDS, list) else [str(config.NEWS_FEEDS)]
	reddit_feeds: List[str] = config.REDDIT_FEEDS if isinstance(config.REDDIT_FEEDS, list) else [str(config.REDDIT_FEEDS)]

	if not skip_news:
		logger.info("Collecting news feeds", extra={"feeds": news_feeds})
		stats["news"] = collect_news(news_feeds)

	if not skip_reddit:
		logger.info("Collecting reddit feeds", extra={"feeds": reddit_feeds})
		stats["reddit"] = collect_reddit(reddit_feeds)

	if not skip_price:
		logger.info("Collecting price snapshot")
		stats["price_snapshots"] = collect_price_snapshot()

	logger.info("Collection complete", extra=stats)
	return stats


def main():
	parser = argparse.ArgumentParser(description="Run data collection pipeline")
	parser.add_argument("--skip-news", action="store_true", help="Skip news collection")
	parser.add_argument("--skip-reddit", action="store_true", help="Skip reddit collection")
	parser.add_argument("--skip-price", action="store_true", help="Skip price snapshot collection")

	args = parser.parse_args()

	print("🛰️ Data Collection Pipeline")
	print("=" * 60)
	print(f"Skip news:   {args.skip_news}")
	print(f"Skip reddit: {args.skip_reddit}")
	print(f"Skip price:  {args.skip_price}")
	print()

	stats = run_collect(skip_news=args.skip_news, skip_reddit=args.skip_reddit, skip_price=args.skip_price)

	print("\n📊 Results")
	print("-" * 60)
	print(f"News items saved:        {stats['news']}")
	print(f"Reddit items saved:      {stats['reddit']}")
	print(f"Price snapshots saved:   {stats['price_snapshots']}")
	print("\n" + "=" * 60)


if __name__ == "__main__":
	main()
