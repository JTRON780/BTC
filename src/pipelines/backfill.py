"""
Historical backfill pipeline for BTC price data.

Fetches historical hourly price points from CoinGecko and persists them.

Usage:
	python -m src.pipelines.backfill --hours 72
"""

import argparse
from typing import Dict, Any

from src.core import get_logger, get_settings
from src.data import init_db, save_prices
from src.ingest.price import backfill_prices


logger = get_logger(__name__)


def run_backfill(hours: int = 48) -> Dict[str, Any]:
	config = get_settings()
	init_db(config.DB_URL)

	logger.info("Fetching historical prices", extra={"hours": hours})
	points = backfill_prices(hours)
	saved = save_prices(points) if points else 0
	logger.info("Backfill complete", extra={"fetched": len(points), "saved": saved})
	return {"fetched": len(points), "saved": saved}


def main():
	parser = argparse.ArgumentParser(description="Backfill historical BTC prices")
	parser.add_argument("--hours", type=int, default=48, help="Number of hours to backfill (default: 48)")
	args = parser.parse_args()

	print("📚 Price Backfill Pipeline")
	print("=" * 60)
	print(f"Hours: {args.hours}")
	print()

	stats = run_backfill(hours=args.hours)

	print("\n📊 Results")
	print("-" * 60)
	print(f"Fetched points: {stats['fetched']}")
	print(f"Saved points:   {stats['saved']}")
	print("\n" + "=" * 60)


if __name__ == "__main__":
	main()
