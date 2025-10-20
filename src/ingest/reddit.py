"""
Reddit RSS feed collector for the BTC sentiment analysis application.

This module fetches and normalizes Reddit RSS feeds into a standard format
compatible with the RawItem schema.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse
import time

import feedparser

from src.core import get_logger

logger = get_logger(__name__)


def fetch_reddit_feeds(feeds: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch and parse Reddit RSS feeds.
    
    Downloads RSS feeds from the provided URLs and normalizes the entries
    into a standard format matching the RawItem schema.
    
    Args:
        feeds: List of Reddit subreddit names (e.g., ['bitcoin', 'cryptocurrency'])
               Will be converted to RSS URLs automatically
               
    Returns:
        List of dictionaries with normalized fields:
        - id: Hash of the item URL (ensures uniqueness)
        - source: Hostname from the URL
        - ts: Published timestamp in UTC
        - title: Post title
        - text: Post content/summary
        - url: Original post URL
        
    Example:
        >>> feeds = ['bitcoin', 'cryptocurrency']
        >>> items = fetch_reddit_feeds(feeds)
        >>> print(f"Fetched {len(items)} items")
    """
    all_items = []
    
    for feed in feeds:
        try:
            # Convert subreddit name to RSS URL if needed
            if not feed.startswith('http'):
                feed_url = f"https://www.reddit.com/r/{feed}/.rss"
            else:
                feed_url = feed
            
            logger.info(f"Fetching feed", extra={'feed_url': feed_url})
            
            # Parse the RSS feed
            parsed_feed = feedparser.parse(feed_url)
            
            # Check for errors
            if hasattr(parsed_feed, 'bozo') and parsed_feed.bozo:
                logger.warning(
                    f"Feed parse warning",
                    extra={
                        'feed_url': feed_url,
                        'error': str(getattr(parsed_feed, 'bozo_exception', 'Unknown error'))
                    }
                )
            
            # Process each entry
            feed_items = []
            for entry in parsed_feed.entries:
                try:
                    item = _normalize_entry(entry, feed_url)
                    if item:
                        feed_items.append(item)
                except Exception as e:
                    logger.error(
                        f"Error normalizing entry",
                        extra={
                            'feed_url': feed_url,
                            'entry_id': getattr(entry, 'id', 'unknown'),
                            'error': str(e)
                        }
                    )
                    continue
            
            logger.info(
                f"Fetched items from feed",
                extra={
                    'feed_url': feed_url,
                    'count': len(feed_items)
                }
            )
            
            all_items.extend(feed_items)
            
        except Exception as e:
            logger.error(
                f"Error fetching feed",
                extra={
                    'feed': feed,
                    'error': str(e)
                }
            )
            continue
    
    logger.info(
        f"Total items fetched",
        extra={
            'total_count': len(all_items),
            'feeds_count': len(feeds)
        }
    )
    
    return all_items


def _normalize_entry(entry: Any, feed_url: str) -> Dict[str, Any] | None:
    """
    Normalize a feed entry into RawItem format.
    
    Args:
        entry: feedparser entry object
        feed_url: URL of the feed (for source identification)
        
    Returns:
        Dictionary with normalized fields, or None if entry is invalid
    """
    # Get URL (link)
    url = entry.get('link', '')
    if not url:
        logger.warning("Entry missing link, skipping")
        return None
    
    # Generate unique ID from URL hash
    item_id = hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
    
    # Extract source from URL
    parsed_url = urlparse(url)
    source = parsed_url.hostname or 'reddit'
    
    # Get title
    title = entry.get('title', '').strip()
    
    # Get text content (try summary, then content, then description)
    text = ''
    if hasattr(entry, 'summary'):
        text = entry.summary
    elif hasattr(entry, 'content'):
        if isinstance(entry.content, list) and len(entry.content) > 0:
            text = entry.content[0].get('value', '')
        else:
            text = str(entry.content)
    elif hasattr(entry, 'description'):
        text = entry.description
    
    # Clean HTML tags from text if present
    import re
    text = re.sub(r'<[^>]+>', '', text).strip()
    
    # Get published timestamp
    ts = None
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            ts = datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError) as e:
            logger.warning(f"Error parsing published time: {e}")
    
    if not ts:
        # Fallback to current time if no published time
        ts = datetime.utcnow()
    
    return {
        'id': f"reddit_{item_id}",
        'source': source,
        'ts': ts,
        'title': title,
        'text': text,
        'url': url
    }


if __name__ == "__main__":
    from src.core import get_settings
    
    print("="*60)
    print("Reddit RSS Feed Collector Test")
    print("="*60)
    
    # Get feeds from config
    config = get_settings()
    reddit_feeds = config.REDDIT_FEEDS
    
    # Ensure it's a list (config parses it automatically)
    if isinstance(reddit_feeds, str):
        reddit_feeds = [feed.strip() for feed in reddit_feeds.split(',')]
    
    logger.info("Starting Reddit feed collection")
    logger.info(f"Configured feeds", extra={'feeds': reddit_feeds})
    
    # Fetch feeds
    print(f"\nFetching from {len(reddit_feeds)} subreddit(s)...")
    items = fetch_reddit_feeds(reddit_feeds)
    
    # Display results
    print(f"\n✅ Fetched {len(items)} total items")
    
    if items:
        print("\nSample items:")
        for i, item in enumerate(items[:3], 1):
            print(f"\n  {i}. {item['title'][:60]}...")
            print(f"     Source: {item['source']}")
            print(f"     URL: {item['url'][:50]}...")
            print(f"     Time: {item['ts']}")
            print(f"     Text preview: {item['text'][:100]}...")
    
    # Test with database integration
    print("\n" + "="*60)
    print("Testing database integration")
    print("="*60)
    
    from src.data import init_db, upsert_raw_items
    
    # Initialize in-memory database
    engine = init_db('sqlite:///:memory:')
    
    if items:
        # Save to database
        count = upsert_raw_items(items)
        print(f"\n✅ Saved {count} items to database")
        
        # Verify by retrieving
        from src.data import get_recent_raw_items
        retrieved = get_recent_raw_items(hours=24, source='www.reddit.com')
        print(f"✅ Retrieved {len(retrieved)} items from database")
    
    print("\n" + "="*60)
    print("✅ Reddit feed collector working correctly!")
    print("="*60)
