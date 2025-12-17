"""
Repository pattern implementation for data access layer.

This module provides database operations using SQLAlchemy 2.0 style with
Session contexts. All functions return plain dictionaries rather than ORM objects
for easier serialization and decoupling from the database layer.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, insert, select, Engine, text
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.data.schemas import Base, RawItem, Price, ScoredItem, SentimentIndex


# Global engine instance
_engine: Optional[Engine] = None


def init_db(db_url: str) -> Engine:
    """
    Initialize the database engine and create all tables.
    
    This function creates a SQLAlchemy engine and ensures all tables
    defined in the schema are created in the database.
    
    Args:
        db_url: Database connection URL (e.g., 'sqlite:///btc.db' or PostgreSQL URL)
        
    Returns:
        Engine: SQLAlchemy engine instance
        
    Example:
        >>> engine = init_db('sqlite:///btc.db')
        >>> # Tables are now created and ready to use
    """
    global _engine
    
    _engine = create_engine(db_url, echo=False)
    
    # Create all tables defined in Base metadata
    Base.metadata.create_all(_engine)
    
    # Run migrations
    _run_migrations(_engine)
    
    return _engine


def _run_migrations(engine: Engine) -> None:
    """
    Run database migrations to handle schema updates.
    
    This function handles adding new columns to existing tables
    when they don't exist yet.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    with engine.connect() as conn:
        # Check if sentiment_indices table exists and add missing columns
        inspector_result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='sentiment_indices'")
        ).fetchone()
        
        if inspector_result:
            # Table exists, check for missing columns
            columns_result = conn.execute(
                text("PRAGMA table_info(sentiment_indices)")
            ).fetchall()
            column_names = [row[1] for row in columns_result]
            
            # Add n_positive if missing
            if "n_positive" not in column_names:
                try:
                    conn.execute(text("ALTER TABLE sentiment_indices ADD COLUMN n_positive INTEGER DEFAULT 0"))
                    conn.commit()
                except Exception:
                    # Column might already exist or other issue
                    pass
            
            # Add n_negative if missing
            if "n_negative" not in column_names:
                try:
                    conn.execute(text("ALTER TABLE sentiment_indices ADD COLUMN n_negative INTEGER DEFAULT 0"))
                    conn.commit()
                except Exception:
                    # Column might already exist or other issue
                    pass
            
            # Add directional_bias if missing
            if "directional_bias" not in column_names:
                try:
                    conn.execute(text("ALTER TABLE sentiment_indices ADD COLUMN directional_bias FLOAT"))
                    conn.commit()
                except Exception:
                    # Column might already exist or other issue
                    pass


def get_engine() -> Engine:
    """
    Get the global database engine instance.
    
    Returns:
        Engine: The initialized engine
        
    Raises:
        RuntimeError: If init_db() has not been called yet
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def upsert_raw_items(items: List[Dict[str, Any]]) -> int:
    """
    Insert or update raw items in the database.
    
    Uses INSERT OR IGNORE (SQLite) to handle duplicate primary keys.
    For other databases, this would use ON CONFLICT DO NOTHING.
    
    Args:
        items: List of dictionaries containing raw item data
               Each dict should have keys: id, source, ts, title, text, url
               
    Returns:
        int: Number of items processed
        
    Example:
        >>> items = [
        ...     {
        ...         'id': 'reddit_123',
        ...         'source': 'reddit',
        ...         'ts': datetime.utcnow(),
        ...         'title': 'Bitcoin news',
        ...         'text': 'Content here...',
        ...         'url': 'https://reddit.com/...'
        ...     }
        ... ]
        >>> count = upsert_raw_items(items)
    """
    if not items:
        return 0
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Use SQLite-specific insert with ON CONFLICT IGNORE
        stmt = sqlite_insert(RawItem).values(items)
        stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
        
        session.execute(stmt)
        session.commit()
    
    return len(items)


def get_recent_raw_items(hours: int = 24, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve recent raw items from the database.
    
    Args:
        hours: Number of hours to look back (default: 24)
        source: Optional source filter (e.g., 'reddit', 'news')
        
    Returns:
        List of dictionaries containing raw item data
        
    Example:
        >>> recent_items = get_recent_raw_items(hours=12)
        >>> reddit_items = get_recent_raw_items(hours=24, source='reddit')
    """
    engine = get_engine()
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    with Session(engine) as session:
        # Build query
        stmt = select(RawItem).where(RawItem.ts >= cutoff_time)
        
        if source:
            stmt = stmt.where(RawItem.source == source)
        
        stmt = stmt.order_by(RawItem.ts.desc())
        
        # Execute and convert to dicts
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                'id': item.id,
                'source': item.source,
                'ts': item.ts,
                'title': item.title,
                'text': item.text,
                'url': item.url,
                'created_at': item.created_at
            }
            for item in results
        ]


def save_scores(scored: List[Dict[str, Any]]) -> int:
    """
    Save sentiment scores for analyzed items.
    
    Uses INSERT OR IGNORE to handle duplicates. Updates are not performed
    to preserve the original scoring timestamp.
    
    Args:
        scored: List of dictionaries containing scored item data
                Each dict should have keys: id, polarity, probs_json, ts, source
                
    Returns:
        int: Number of items processed
        
    Example:
        >>> scores = [
        ...     {
        ...         'id': 'reddit_123',
        ...         'polarity': 0.85,
        ...         'probs_json': {'positive': 0.85, 'neutral': 0.10, 'negative': 0.05},
        ...         'ts': datetime.utcnow(),
        ...         'source': 'reddit'
        ...     }
        ... ]
        >>> count = save_scores(scores)
    """
    if not scored:
        return 0
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Use SQLite-specific insert with ON CONFLICT IGNORE
        stmt = sqlite_insert(ScoredItem).values(scored)
        stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
        
        session.execute(stmt)
        session.commit()
    
    return len(scored)


def save_prices(prices: List[Dict[str, Any]]) -> int:
    """
    Save Bitcoin price data.
    
    Uses INSERT OR REPLACE to update existing price data for the same timestamp.
    
    Args:
        prices: List of dictionaries containing price data
                Each dict should have keys: ts, price, volume (optional)
                
    Returns:
        int: Number of items processed
        
    Example:
        >>> price_data = [
        ...     {
        ...         'ts': datetime.utcnow(),
        ...         'price': 67500.50,
        ...         'volume': 28500000000.00
        ...     }
        ... ]
        >>> count = save_prices(price_data)
    """
    if not prices:
        return 0
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Use SQLite-specific insert with ON CONFLICT REPLACE
        stmt = sqlite_insert(Price).values(prices)
        stmt = stmt.on_conflict_do_update(
            index_elements=['ts'],
            set_={'price': stmt.excluded.price, 'volume': stmt.excluded.volume}
        )
        
        session.execute(stmt)
        session.commit()
    
    return len(prices)


def get_recent_prices(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Retrieve recent Bitcoin price data from the database.
    
    Args:
        hours: Number of hours to look back (default: 24)
        
    Returns:
        List of dictionaries containing price data (ts, price, volume)
        
    Example:
        >>> recent_prices = get_recent_prices(hours=48)
        >>> for point in recent_prices:
        ...     print(f"Price at {point['ts']}: ${point['price']:.2f}")
    """
    engine = get_engine()
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    with Session(engine) as session:
        # Build query
        stmt = select(Price).where(Price.ts >= cutoff_time)
        stmt = stmt.order_by(Price.ts.desc())
        
        # Execute and convert to dicts
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                'ts': price.ts,
                'price': price.price,
                'volume': price.volume,
                'created_at': price.created_at
            }
            for price in results
        ]


def get_index(granularity: str, days: int = 7) -> List[Dict[str, Any]]:
    """
    Retrieve sentiment index data for a specific granularity and time range.
    
    Args:
        granularity: Time granularity ('hourly', 'daily', 'weekly', etc.)
        days: Number of days to look back (default: 7)
        
    Returns:
        List of dictionaries containing sentiment index data
        
    Example:
        >>> hourly_data = get_index('hourly', days=7)
        >>> daily_data = get_index('daily', days=30)
    """
    engine = get_engine()
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    with Session(engine) as session:
        # Build query
        stmt = (
            select(SentimentIndex)
            .where(SentimentIndex.granularity == granularity)
            .where(SentimentIndex.ts >= cutoff_time)
            .order_by(SentimentIndex.ts.asc())
        )
        
        # Execute and convert to dicts
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                'ts': item.ts,
                'granularity': item.granularity,
                'raw_value': item.raw_value,
                'smoothed_value': item.smoothed_value,
                'n_posts': item.n_posts
            }
            for item in results
        ]


def save_sentiment_indices(indices: List[Dict[str, Any]]) -> int:
    """
    Save aggregated sentiment index data.
    
    Uses INSERT OR REPLACE to update existing indices for the same ts+granularity.
    
    Args:
        indices: List of dictionaries containing sentiment index data
                 Each dict should have keys: ts, granularity, raw_value, 
                 smoothed_value (optional), n_posts
                 
    Returns:
        int: Number of items processed
        
    Example:
        >>> index_data = [
        ...     {
        ...         'ts': datetime(2025, 10, 15, 12, 0),
        ...         'granularity': 'hourly',
        ...         'raw_value': 0.65,
        ...         'smoothed_value': 0.62,
        ...         'n_posts': 150
        ...     }
        ... ]
        >>> count = save_sentiment_indices(index_data)
    """
    if not indices:
        return 0
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Use SQLite-specific insert with ON CONFLICT REPLACE
        stmt = sqlite_insert(SentimentIndex).values(indices)
        stmt = stmt.on_conflict_do_update(
            index_elements=['ts', 'granularity'],
            set_={
                'raw_value': stmt.excluded.raw_value,
                'smoothed_value': stmt.excluded.smoothed_value,
                'n_posts': stmt.excluded.n_posts
            }
        )
        
        session.execute(stmt)
        session.commit()
    
    return len(indices)


def get_prices(days: int = 7) -> List[Dict[str, Any]]:
    """
    Retrieve price data for a specific time range.
    
    Args:
        days: Number of days to look back (default: 7)
        
    Returns:
        List of dictionaries containing price data
        
    Example:
        >>> prices = get_prices(days=30)
    """
    engine = get_engine()
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    with Session(engine) as session:
        # Build query
        stmt = (
            select(Price)
            .where(Price.ts >= cutoff_time)
            .order_by(Price.ts.asc())
        )
        
        # Execute and convert to dicts
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                'ts': item.ts,
                'price': item.price,
                'volume': item.volume
            }
            for item in results
        ]


if __name__ == "__main__":
    # Demonstration and testing of repository functions
    from src.core import get_logger
    
    logger = get_logger(__name__)
    
    print("="*60)
    print("Testing Repository Functions")
    print("="*60)
    
    # Initialize database
    logger.info("Initializing test database")
    engine = init_db('sqlite:///test_stores.db')
    print(f"\n✅ Database initialized: {engine.url}")
    
    # Test upsert_raw_items
    logger.info("Testing upsert_raw_items")
    test_items = [
        {
            'id': 'reddit_001',
            'source': 'reddit',
            'ts': datetime(2025, 10, 19, 12, 0),
            'title': 'Bitcoin breaks $70k!',
            'text': 'BTC just hit a new milestone...',
            'url': 'https://reddit.com/r/bitcoin/001'
        },
        {
            'id': 'news_001',
            'source': 'news',
            'ts': datetime(2025, 10, 19, 13, 0),
            'title': 'Institutional adoption grows',
            'text': 'Major banks are now offering...',
            'url': 'https://example.com/news/001'
        }
    ]
    count = upsert_raw_items(test_items)
    print(f"\n✅ Upserted {count} raw items")
    
    # Test duplicate handling
    count = upsert_raw_items(test_items)
    print(f"✅ Duplicate upsert handled: {count} items (no error)")
    
    # Test get_recent_raw_items
    logger.info("Testing get_recent_raw_items")
    recent = get_recent_raw_items(hours=24)
    print(f"\n✅ Retrieved {len(recent)} recent items")
    if recent:
        print(f"   Sample: {recent[0]['title']}")
    
    # Test save_scores
    logger.info("Testing save_scores")
    test_scores = [
        {
            'id': 'reddit_001',
            'polarity': 0.85,
            'probs_json': {'positive': 0.85, 'neutral': 0.10, 'negative': 0.05},
            'ts': datetime(2025, 10, 19, 12, 5),
            'source': 'reddit'
        }
    ]
    count = save_scores(test_scores)
    print(f"\n✅ Saved {count} scored items")
    
    # Test save_prices
    logger.info("Testing save_prices")
    test_prices = [
        {
            'ts': datetime(2025, 10, 19, 12, 0),
            'price': 70250.50,
            'volume': 31000000000.00
        },
        {
            'ts': datetime(2025, 10, 19, 13, 0),
            'price': 70500.00,
            'volume': 32000000000.00
        }
    ]
    count = save_prices(test_prices)
    print(f"\n✅ Saved {count} price records")
    
    # Test get_prices
    prices = get_prices(days=1)
    print(f"✅ Retrieved {len(prices)} price records")
    if prices:
        print(f"   Latest: ${prices[-1]['price']:.2f}")
    
    # Test save_sentiment_indices
    logger.info("Testing save_sentiment_indices")
    test_indices = [
        {
            'ts': datetime(2025, 10, 19, 12, 0),
            'granularity': 'hourly',
            'raw_value': 0.65,
            'smoothed_value': 0.62,
            'n_posts': 150
        },
        {
            'ts': datetime(2025, 10, 19, 13, 0),
            'granularity': 'hourly',
            'raw_value': 0.70,
            'smoothed_value': 0.65,
            'n_posts': 200
        }
    ]
    count = save_sentiment_indices(test_indices)
    print(f"\n✅ Saved {count} sentiment indices")
    
    # Test get_index
    logger.info("Testing get_index")
    indices = get_index('hourly', days=1)
    print(f"\n✅ Retrieved {len(indices)} hourly indices")
    if indices:
        print(f"   Latest: raw={indices[-1]['raw_value']:.3f}, smoothed={indices[-1]['smoothed_value']:.3f}")
    
    print("\n" + "="*60)
    print("✅ All repository functions working correctly!")
    print("="*60)
    
    # Cleanup
    import os
    os.remove('test_stores.db')
    logger.info("Test database cleaned up")
