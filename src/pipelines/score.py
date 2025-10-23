"""
Sentiment scoring pipeline for raw items.

This script loads unscored raw items from the database, runs sentiment
analysis using the NLP model, and persists the results.
"""

import argparse
import time
from datetime import datetime
from typing import List, Dict, Any
import json

from src.core import get_logger, get_settings
from src.data import get_recent_raw_items, save_scores, init_db
from src.nlp import clean_text, compose_text, SentimentModel

logger = get_logger(__name__)


def get_unscored_items(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Retrieve recent raw items that haven't been scored yet.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        List of raw item dictionaries
    """
    logger.info(f"Fetching unscored items", extra={'hours': hours})
    
    # Get recent raw items
    items = get_recent_raw_items(hours=hours)
    
    logger.info(f"Found raw items", extra={'count': len(items)})
    
    return items


def score_items(items: List[Dict[str, Any]], model: SentimentModel) -> List[Dict[str, Any]]:
    """
    Score sentiment for a batch of raw items.
    
    Args:
        items: List of raw item dictionaries with 'title' and 'text' fields
        model: Loaded sentiment model
        
    Returns:
        List of scored item dictionaries with sentiment probabilities and polarity
    """
    if not items:
        return []
    
    logger.info(f"Preparing items for scoring", extra={'count': len(items)})
    
    # Prepare texts for batch prediction
    texts = []
    for item in items:
        # Compose title + text
        composed = compose_text(item.get('title', ''), item.get('text', ''))
        # Clean the text
        cleaned = clean_text(composed)
        texts.append(cleaned)
    
    logger.info(f"Running batch prediction", extra={'batch_size': len(texts)})
    
    # Run batch prediction
    start_time = time.time()
    predictions = model.predict(texts)
    elapsed = time.time() - start_time
    
    avg_latency = elapsed / len(texts) if texts else 0
    
    logger.info(
        f"Prediction complete",
        extra={
            'count': len(predictions),
            'total_time': f"{elapsed:.2f}s",
            'avg_latency': f"{avg_latency:.3f}s"
        }
    )
    
    # Build scored items
    scored = []
    for item, probs in zip(items, predictions):
        # Compute polarity: pos - neg
        polarity = probs['pos'] - probs['neg']
        
        scored_item = {
            'id': item['id'],
            'polarity': polarity,
            'probs_json': json.dumps(probs),  # Store as JSON string
            'ts': item['ts'],
            'source': item['source']
        }
        scored.append(scored_item)
    
    return scored


def run_scoring_pipeline(since_hours: int = 24) -> Dict[str, Any]:
    """
    Run the complete scoring pipeline.
    
    Args:
        since_hours: Number of hours to look back for unscored items
        
    Returns:
        Dictionary with pipeline statistics
    """
    start_time = time.time()
    
    logger.info(
        f"Starting scoring pipeline",
        extra={'since_hours': since_hours}
    )
    
    # Initialize database
    config = get_settings()
    init_db(config.DB_URL)
    
    # Load sentiment model
    logger.info("Loading sentiment model")
    model = SentimentModel()
    
    # Get unscored items
    items = get_unscored_items(hours=since_hours)
    
    if not items:
        logger.info("No items to score")
        return {
            'items_fetched': 0,
            'items_scored': 0,
            'items_saved': 0,
            'total_time': 0,
            'avg_latency': 0
        }
    
    # Score items
    scored = score_items(items, model)
    
    # Save to database
    logger.info(f"Saving scored items", extra={'count': len(scored)})
    saved_count = save_scores(scored)
    
    # Calculate statistics
    total_time = time.time() - start_time
    avg_latency = total_time / len(items) if items else 0
    
    # Calculate average polarity
    if scored:
        avg_polarity = sum(s['polarity'] for s in scored) / len(scored)
    else:
        avg_polarity = 0.0
    
    stats = {
        'items_fetched': len(items),
        'items_scored': len(scored),
        'items_saved': saved_count,
        'total_time': total_time,
        'avg_latency': avg_latency,
        'avg_polarity': avg_polarity
    }
    
    logger.info(
        f"Pipeline complete",
        extra=stats
    )
    
    return stats


def main():
    """
    CLI entry point for the scoring pipeline.
    """
    parser = argparse.ArgumentParser(
        description='Run sentiment scoring pipeline on recent raw items'
    )
    parser.add_argument(
        '--since-hours',
        type=int,
        default=24,
        help='Number of hours to look back for unscored items (default: 24)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    print("🧠 Sentiment Scoring Pipeline")
    print("=" * 60)
    print(f"Looking back: {args.since_hours} hours")
    print()
    
    try:
        # Run pipeline
        stats = run_scoring_pipeline(since_hours=args.since_hours)
        
        # Print results
        print("\n📊 Pipeline Results:")
        print("-" * 60)
        print(f"Items fetched:  {stats['items_fetched']}")
        print(f"Items scored:   {stats['items_scored']}")
        print(f"Items saved:    {stats['items_saved']}")
        print(f"Total time:     {stats['total_time']:.2f}s")
        print(f"Avg latency:    {stats['avg_latency']:.3f}s per item")
        print(f"Avg polarity:   {stats['avg_polarity']:+.3f}")
        print()
        
        # Interpret average polarity
        if stats['avg_polarity'] > 0.1:
            sentiment_label = "POSITIVE 📈"
        elif stats['avg_polarity'] < -0.1:
            sentiment_label = "NEGATIVE 📉"
        else:
            sentiment_label = "NEUTRAL ➡️"
        
        print(f"Overall sentiment: {sentiment_label}")
        print()
        print("=" * 60)
        print("✅ Pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed", extra={'error': str(e)})
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
