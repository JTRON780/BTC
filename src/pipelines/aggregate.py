"""
Aggregation pipeline: compute hourly and daily sentiment rollups.

This script queries `scored_items`, groups by time window and source,
computes a weighted average polarity (news=1.2, reddit=1.0), and
persists results to the `sentiment_indices` table via `save_sentiment_indices()`.
"""

import argparse
from collections import defaultdict
from datetime import datetime, timedelta
import time
from typing import Dict, List, Tuple, Any, cast

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core import get_logger, get_settings
from src.data import init_db, get_engine, ScoredItem, save_sentiment_indices, get_index

logger = get_logger(__name__)


WEIGHTS = {
	'news': 1.2,
	'reddit': 1.0,
}


def _window_ts(ts: datetime, granularity: str) -> datetime:
	"""Return the window-aligned timestamp for granularity.
	For 'hourly' -> round down to hour. For 'daily' -> round down to midnight.
	"""
	if granularity == 'hourly':
		return ts.replace(minute=0, second=0, microsecond=0)
	elif granularity == 'daily':
		return ts.replace(hour=0, minute=0, second=0, microsecond=0)
	else:
		raise ValueError(f"Unsupported granularity: {granularity}")


def _weight_for_source(source: str) -> float:
    """Return weight for a given source string."""
    if not source:
        return 1.0
    s = source.lower()
    if 'news' in s:
        return WEIGHTS['news']
    if 'reddit' in s:
        return WEIGHTS['reddit']
    # default
    return 1.0


def _apply_ewma_smoothing(data: List[Dict[str, Any]], alpha: float = 0.2) -> List[Dict[str, Any]]:
    """
    Apply exponential weighted moving average smoothing to raw_value by source.
    
    Args:
        data: List of dicts with keys: ts, source, granularity, raw_value, n_posts
              Must be sorted by (source, ts)
        alpha: Smoothing parameter (0 < alpha <= 1). Higher values give more weight to recent observations.
        
    Returns:
        List of dicts with added 'smoothed_value' field
    """
    if not data:
        return []
    
    # Group by source for independent EWMA computation
    by_source: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in data:
        by_source[item['source']].append(item)
    
    result = []
    
    for source, items in by_source.items():
        # Sort by timestamp within source (should already be sorted)
        items.sort(key=lambda x: x['ts'])
        
        # Get existing smoothed values from database to maintain continuity
        existing_indices = []
        if items:
            try:
                # Look back further to get previous smoothed values for continuity
                lookback_days = 30  # Look back 30 days for existing data
                existing_indices = get_index(items[0]['granularity'], days=lookback_days)
                existing_indices = [idx for idx in existing_indices if idx['ts'] < items[0]['ts']]
                existing_indices.sort(key=lambda x: x['ts'])
            except Exception as e:
                logger.warning(f"Could not fetch existing indices for continuity", extra={'error': str(e)})
                existing_indices = []
        
        # Initialize EWMA
        smoothed_value = None
        if existing_indices:
            # Use the most recent existing smoothed value as seed
            last_existing = existing_indices[-1]
            smoothed_value = last_existing.get('smoothed_value')
            if smoothed_value is None:
                smoothed_value = last_existing.get('raw_value', 0.0)
        
        # Compute EWMA for current batch
        for item in items:
            raw_value = item['raw_value']
            
            if smoothed_value is None:
                # First value: initialize EWMA with raw value
                smoothed_value = raw_value
            else:
                # EWMA formula: S_t = α * X_t + (1 - α) * S_{t-1}
                smoothed_value = alpha * raw_value + (1 - alpha) * smoothed_value
            
            # Add smoothed value to item
            item_copy = item.copy()
            item_copy['smoothed_value'] = float(smoothed_value)
            result.append(item_copy)
    
    # Sort final result by timestamp
    result.sort(key=lambda x: x['ts'])
    
    return result
def compute_rollups(granularity: str = 'hourly', days: int = 7) -> List[Dict[str, Any]]:
    """
    Compute sentiment rollups for the past `days` days at the given granularity.
    
    Now includes EWMA smoothing (α=0.2) for each time series by source.

    Returns list of dicts suitable for `save_sentiment_indices`:
      { 'ts': datetime, 'granularity': str, 'raw_value': float, 'smoothed_value': float, 'n_posts': int }
    """
    if granularity not in ('hourly', 'daily'):
        raise ValueError("granularity must be 'hourly' or 'daily'")

    cutoff = datetime.utcnow() - timedelta(days=days)

    engine = get_engine()

    # Query scored items since cutoff
    with Session(engine) as session:
        stmt = select(ScoredItem).where(ScoredItem.ts >= cutoff)
        rows = session.execute(stmt).scalars().all()

    logger.info("Fetched scored items for aggregation", extra={'count': len(rows)})

    # Group by (window_ts, source)
    groups: Dict[Tuple[datetime, str], List[Tuple[float, float]]] = defaultdict(list)
    # store list of (polarity, weight)

    for r in rows:
        try:
            ts_val = cast(datetime, r.ts)
            window = _window_ts(ts_val, granularity)
        except Exception:
            continue
        source_val = cast(str, r.source) if getattr(r, 'source', None) is not None else 'unknown'
        weight = _weight_for_source(source_val)
        polarity_val = float(cast(float, r.polarity))
        groups[(window, source_val)].append((polarity_val, weight))

    logger.info("Computed groups for aggregation", extra={'groups': len(groups)})

    # Compute weighted average per group
    raw_results = []
    for (window, source), values in groups.items():
        total_weight = sum(w for (_, w) in values)
        if total_weight == 0:
            raw_value = 0.0
        else:
            weighted_sum = sum(p * w for (p, w) in values)
            raw_value = weighted_sum / total_weight

        n_posts = len(values)

        raw_results.append({
            'ts': window,
            'source': source,
            'granularity': granularity,
            'raw_value': float(raw_value),
            'n_posts': n_posts,
        })

    # Sort by source, then by ts for EWMA computation
    raw_results.sort(key=lambda x: (x['source'], x['ts']))

    # Apply EWMA smoothing per source
    results_with_ewma = _apply_ewma_smoothing(raw_results, alpha=0.2)

    # Remove source field and sort by timestamp for final output
    final_results = []
    for item in results_with_ewma:
        final_results.append({
            'ts': item['ts'],
            'granularity': item['granularity'],
            'raw_value': item['raw_value'],
            'smoothed_value': item['smoothed_value'],
            'n_posts': item['n_posts'],
        })

    # Sort results by ts for final output
    final_results.sort(key=lambda x: x['ts'])

    return final_results
def run_aggregation(granularity: str = 'hourly', days: int = 7) -> Dict[str, Any]:
	start = time.time()

	logger.info(f"Starting aggregation", extra={'granularity': granularity, 'days': days})

	config = get_settings()
	init_db(config.DB_URL)

	indices = compute_rollups(granularity=granularity, days=days)

	if not indices:
		logger.info("No indices to save")
		return {'saved': 0, 'computed': 0, 'time_s': 0.0, 'avg_latency_s': 0.0}

	saved = save_sentiment_indices(indices)

	total_time = time.time() - start
	avg_latency = total_time / len(indices) if indices else 0.0

	logger.info("Aggregation complete", extra={'computed': len(indices), 'saved': saved, 'time_s': total_time, 'avg_latency_s': avg_latency})

	return {'saved': saved, 'computed': len(indices), 'time_s': total_time, 'avg_latency_s': avg_latency}


def main():
	parser = argparse.ArgumentParser(description='Compute sentiment rollups and persist indices')
	parser.add_argument('--granularity', type=str, choices=['hourly', 'daily'], default='hourly')
	parser.add_argument('--days', type=int, default=7, help='Number of days to look back')

	args = parser.parse_args()

	print("📈 Sentiment Aggregation")
	print("=" * 60)
	print(f"Granularity: {args.granularity}")
	print(f"Days: {args.days}")
	print()

	stats = run_aggregation(granularity=args.granularity, days=args.days)

	print("\n📊 Results:")
	print("-" * 60)
	print(f"Computed indices: {stats['computed']}")
	print(f"Saved indices:    {stats['saved']}")
	print(f"Total time:       {stats['time_s']:.2f}s")
	print(f"Avg latency:      {stats['avg_latency_s']:.3f}s per index")
	print("\n" + "=" * 60)


if __name__ == '__main__':
	main()
