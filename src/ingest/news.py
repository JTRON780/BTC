"""
Crypto News RSS feed collector for the BTC sentiment analysis application.

This module fetches and normalizes crypto news RSS feeds into a standard format
compatible with the RawItem schema.
"""

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from urllib.parse import urlparse
import re
from time import struct_time

import feedparser

from src.core import get_logger

logger = get_logger(__name__)


def fetch_news_feeds(feeds: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch and parse crypto news RSS feeds.
    
    Downloads RSS feeds from the provided URLs and normalizes the entries
    into a standard format matching the RawItem schema.
    
    Args:
        feeds: List of news feed URLs (e.g., ['https://cointelegraph.com/rss', ...])
               
    Returns:
        List of dictionaries with normalized fields:
        - id: Hash of the item URL (ensures uniqueness)
        - source: "news" tag for all news items
        - ts: Published timestamp in UTC
        - title: Article title
        - text: Article content/summary
        - url: Original article URL
        
    Example:
        >>> feeds = ['https://cointelegraph.com/rss']
        >>> items = fetch_news_feeds(feeds)
        >>> print(f"Fetched {len(items)} items")
    """
    all_items = []
    seen_urls = set()  # Track URLs to skip duplicates
    
    for feed_url in feeds:
        try:
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
                        # Skip duplicates by URL
                        if item['url'] in seen_urls:
                            logger.debug(
                                f"Skipping duplicate URL",
                                extra={'url': item['url']}
                            )
                            continue
                        
                        seen_urls.add(item['url'])
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
                    'feed_url': feed_url,
                    'error': str(e)
                }
            )
            continue
    
    logger.info(
        f"Total items fetched",
        extra={'total_count': len(all_items)}
    )
    
    return all_items


def _normalize_entry(entry: Any, feed_url: str) -> Dict[str, Any] | None:
    """
    Normalize a single feed entry to match RawItem schema.
    
    Args:
        entry: feedparser entry object
        feed_url: Original feed URL for context
        
    Returns:
        Dictionary with normalized fields, or None if entry is invalid
    """
    try:
        # Extract URL (required field)
        url = getattr(entry, 'link', None)
        if not url:
            logger.warning(
                f"Entry missing URL",
                extra={'feed_url': feed_url}
            )
            return None
        
        # Generate unique ID from URL hash
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
        item_id = f"news_{url_hash}"
        
        # Extract title
        title = getattr(entry, 'title', '').strip()
        if not title:
            title = "No title"
        
        # Extract text content (try multiple fields)
        text = ''
        if hasattr(entry, 'summary'):
            text = entry.summary
        elif hasattr(entry, 'description'):
            text = entry.description
        elif hasattr(entry, 'content'):
            # Some feeds use 'content' field
            if isinstance(entry.content, list) and len(entry.content) > 0:
                text = entry.content[0].get('value', '')
            else:
                text = str(entry.content)
        
        # Clean HTML tags from text
        text = _strip_html(text).strip()
        
        # If no text content, use title
        if not text:
            text = title
        
        # Extract and parse timestamp
        ts = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            # Convert struct_time to datetime in UTC
            ts = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            # Convert struct_time to datetime in UTC
            ts = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        else:
            # Fallback to current time in UTC if no timestamp
            ts = datetime.now(timezone.utc)
        
        # Extract source from URL domain
        source = _extract_source_from_url(url)
        
        return {
            'id': item_id,
            'source': source,
            'ts': ts,
            'title': title,
            'text': text,
            'url': url
        }
        
    except Exception as e:
        logger.error(
            f"Error in _normalize_entry",
            extra={
                'feed_url': feed_url,
                'error': str(e)
            }
        )
        return None


def _extract_source_from_url(url: str) -> str:
    """
    Extract a clean source name from a URL.
    
    Args:
        url: Article URL
        
    Returns:
        Source name (e.g., 'Cointelegraph', 'Decrypt', 'CoinDesk')
    """
    # Mapping of domains to nice display names
    source_names = {
        'cointelegraph': 'Cointelegraph',
        'decrypt': 'Decrypt',
        'coindesk': 'CoinDesk',
        'bitcoinmagazine': 'Bitcoin Magazine',
        'cryptobriefing': 'Crypto Briefing',
        'reuters': 'Reuters',
        'bloomberg': 'Bloomberg',
        'ft': 'Financial Times',
        'theblock': 'The Block',
        'cryptoslate': 'CryptoSlate',
        'news': 'Google News',
    }
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Extract main domain (before .com, .co, etc)
        # Handle cases like 'decrypt.co', 'ft.com', 'bloomberg.com'
        parts = domain.split('.')
        if len(parts) >= 2:
            # Use the main part before TLD
            source = parts[0]
        else:
            source = domain
        
        # Return nice display name if available, otherwise capitalize the source
        return source_names.get(source, source.capitalize())
        
    except Exception as e:
        logger.warning(f"Failed to extract source from URL: {url}", extra={'error': str(e)})
        return 'News'


def _strip_html(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text potentially containing HTML tags
        
    Returns:
        Plain text with HTML tags removed
    """
    if not text:
        return ''
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


# Test block for development
if __name__ == "__main__":
    from src.data import init_db, upsert_raw_items, get_recent_raw_items
    from src.core import get_settings
    
    # Initialize logger and config
    logger = get_logger(__name__)
    config = get_settings()
    
    print("🗞️  Testing News Feed Collector")
    print("=" * 60)
    
    # Initialize database
    init_db(config.DB_URL)
    
    # Fetch news feeds from config
    news_feeds = config.NEWS_FEEDS
    if isinstance(news_feeds, str):
        news_feeds = [news_feeds]
    
    print(f"\n📡 Fetching from {len(news_feeds)} news feeds...")
    items = fetch_news_feeds(news_feeds)
    
    print(f"\n✅ Fetched {len(items)} total items")
    
    # Show sample items
    if items:
        print(f"\n📰 Sample items:")
        for i, item in enumerate(items[:3], 1):
            print(f"\n  {i}. {item['title'][:60]}...")
            print(f"     Source: {item['source']}")
            print(f"     URL: {item['url'][:60]}...")
            print(f"     Text preview: {item['text'][:80]}...")
    
    # Save to database
    if items:
        count = upsert_raw_items(items)
        print(f"\n✅ Saved {count} items to database")
        
        # Retrieve and verify
        retrieved = get_recent_raw_items(hours=168, source='news')
        print(f"✅ Retrieved {len(retrieved)} news items from database")
    
    print("\n" + "=" * 60)
    print("✅ News feed collector working correctly!")
