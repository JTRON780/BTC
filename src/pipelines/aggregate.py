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
    if s.startswith('r/'):
        return WEIGHTS['reddit']
    if 'news' in s:
        return WEIGHTS['news']
    if 'reddit' in s:
        return WEIGHTS['reddit']
    # Pipeline only ingests news and reddit; treat unknown as news.
    return WEIGHTS['news']


def _apply_ewma_smoothing(data: List[Dict[str, Any]], alpha: float = 0.2) -> List[Dict[str, Any]]:
    """
    Apply exponential weighted moving average smoothing to raw_value by source.
    
    For daily granularity, each day is smoothed independently (no carryover from previous days).
    For hourly granularity, smoothing carries across hours within the same day, but resets at midnight.
    
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
    granularity = data[0].get('granularity', 'daily') if data else 'daily'
    
    for source, items in by_source.items():
        # Sort by timestamp within source (should already be sorted)
        items.sort(key=lambda x: x['ts'])
        
        # For daily granularity: each day is independent (no smoothing carryover from previous days)
        # For hourly granularity: smoothing carries within each day but resets at midnight
        if granularity == 'daily':
            # Daily mode: each day's smoothed value = raw value (no temporal smoothing)
            for item in items:
                item_copy = item.copy()
                item_copy['smoothed_value'] = item['raw_value']  # Daily sentiment is unsmoothed
                result.append(item_copy)
        else:
            # Hourly mode: apply EWMA within each day, reset at midnight
            current_day = None
            smoothed_value = None
            
            for item in items:
                item_ts = item['ts']
                item_day = item_ts.date()
                
                # Reset smoothed value at day boundary
                if current_day is not None and item_day != current_day:
                    smoothed_value = None
                
                current_day = item_day
                raw_value = item['raw_value']
                
                if smoothed_value is None:
                    # First value of the day: initialize with raw value
                    smoothed_value = raw_value
                else:
                    # EWMA formula: S_t = α * X_t + (1 - α) * S_{t-1}
                    smoothed_value = alpha * raw_value + (1 - alpha) * smoothed_value
                
                item_copy = item.copy()
                item_copy['smoothed_value'] = float(smoothed_value)
                result.append(item_copy)
    
    # Sort final result by timestamp
    result.sort(key=lambda x: x['ts'])
    
    return result
def compute_rollups(granularity: str = 'hourly', days: int = 7) -> List[Dict[str, Any]]:
    """
    Compute sentiment rollups for the past `days` days at the given granularity.
    
    Now includes EWMA smoothing (α=0.2) for each time series by source,
    and directional bias calculation.

    Returns list of dicts suitable for `save_sentiment_indices`:
      { 'ts': datetime, 'granularity': str, 'raw_value': float, 'smoothed_value': float, 
        'n_posts': int, 'n_positive': int, 'n_negative': int, 'directional_bias': float }
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

    # Group across all sources per time window
    # Store list of (polarity, weight) and track positive/negative counts
    groups: Dict[datetime, List[Tuple[float, float]]] = defaultdict(list)
    polarity_signs: Dict[datetime, List[int]] = defaultdict(list)  # Track sign of each polarity

    for r in rows:
        try:
            ts_val = cast(datetime, r.ts)
            window = _window_ts(ts_val, granularity)
        except Exception:
            continue
        source_val = cast(str, r.source) if getattr(r, 'source', None) is not None else 'unknown'
        weight = _weight_for_source(source_val)
        polarity_val = float(cast(float, r.polarity))
        groups[window].append((polarity_val, weight))
        
        # Track positive/negative: 1 if polarity > 0, -1 if < 0, 0 if == 0
        sign = 1 if polarity_val > 0 else (-1 if polarity_val < 0 else 0)
        polarity_signs[window].append(sign)

    logger.info("Computed groups for aggregation", extra={'groups': len(groups)})

    # Compute weighted average per window and directional bias
    raw_series = []
    for window, values in groups.items():
        total_weight = sum(w for (_, w) in values)
        if total_weight == 0:
            raw_value = 0.0
        else:
            weighted_sum = sum(p * w for (p, w) in values)
            raw_value = weighted_sum / total_weight

        n_posts = len(values)
        
        # Calculate directional bias
        signs = polarity_signs[window]
        n_positive = sum(1 for s in signs if s > 0)
        n_negative = sum(1 for s in signs if s < 0)
        directional_bias = (n_positive - n_negative) / n_posts if n_posts > 0 else 0.0

        raw_series.append({
            'ts': window,
            'source': 'combined',  # placeholder for EWMA grouping
            'granularity': granularity,
            'raw_value': float(raw_value),
            'n_posts': n_posts,
            'n_positive': n_positive,
            'n_negative': n_negative,
            'directional_bias': float(directional_bias),
        })

    # Sort by timestamp
    raw_series.sort(key=lambda x: x['ts'])

    # Apply EWMA smoothing on combined series
    results_with_ewma = _apply_ewma_smoothing(raw_series, alpha=0.2)

    # Prepare final output without source
    final_results = []
    for item in results_with_ewma:
        final_results.append({
            'ts': item['ts'],
            'granularity': item['granularity'],
            'raw_value': item['raw_value'],
            'smoothed_value': item['smoothed_value'],
            'n_posts': item['n_posts'],
            'n_positive': item['n_positive'],
            'n_negative': item['n_negative'],
            'directional_bias': item['directional_bias'],
        })

    # Sort results by ts
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
