"""
SQLAlchemy ORM models for the BTC sentiment analysis application.

This module defines the database schema using SQLAlchemy's declarative base,
including models for raw data items, price data, scored sentiment items,
and aggregated sentiment indices.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, Float
from sqlalchemy.orm import declarative_base

# Create the declarative base for all models
Base = declarative_base()


class RawItem(Base):
    """
    Raw data items collected from various sources (Reddit, news feeds, etc.).
    
    This table stores unprocessed items before sentiment analysis.
    
    Attributes:
        id: Unique identifier for the item (primary key)
        source: Source of the item (e.g., 'reddit', 'news', 'twitter')
        ts: Timestamp when the item was created/published
        title: Title or headline of the item
        text: Full text content of the item
        url: Source URL where the item was found
        created_at: Timestamp when the record was inserted into the database
    """
    
    __tablename__ = "raw_items"
    
    id = Column(Text, primary_key=True, nullable=False)
    source = Column(Text, nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    title = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        """Return a string representation of the RawItem for debugging."""
        title_preview = self.title[:50] if self.title is not None else None
        return (
            f"<RawItem(id='{self.id}', source='{self.source}', "
            f"ts={self.ts}, title='{title_preview}...')>"
        )


class Price(Base):
    """
    Bitcoin price data from external APIs (e.g., CoinGecko).
    
    This table stores historical price and volume data for correlation analysis.
    
    Attributes:
        ts: Timestamp of the price data point (primary key)
        price: Bitcoin price in USD
        volume: Trading volume in USD
    """
    
    __tablename__ = "prices"
    
    ts = Column(DateTime, primary_key=True, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    
    def __repr__(self) -> str:
        """Return a string representation of the Price for debugging."""
        volume_str = f"${self.volume:.2f}" if self.volume is not None else "N/A"
        return (
            f"<Price(ts={self.ts}, price=${self.price:.2f}, "
            f"volume={volume_str})>"
        )


class ScoredItem(Base):
    """
    Items that have been processed through sentiment analysis.
    
    This table stores the sentiment scores and probability distributions
    for each analyzed item.
    
    Attributes:
        id: Unique identifier matching the RawItem (primary key)
        polarity: Sentiment polarity score (-1.0 to 1.0, or custom range)
        probs_json: JSON object containing probability distribution across sentiment classes
        ts: Timestamp when the item was scored
        source: Source of the item (for quick filtering)
    """
    
    __tablename__ = "scored_items"
    
    id = Column(Text, primary_key=True, nullable=False)
    polarity = Column(Float, nullable=False)
    probs_json = Column(JSON, nullable=True)
    ts = Column(DateTime, nullable=False, index=True)
    source = Column(Text, nullable=False, index=True)
    
    def __repr__(self) -> str:
        """Return a string representation of the ScoredItem for debugging."""
        return (
            f"<ScoredItem(id='{self.id}', source='{self.source}', "
            f"polarity={self.polarity:.3f}, ts={self.ts})>"
        )


class SentimentIndex(Base):
    """
    Aggregated sentiment indices at various time granularities.
    
    This table stores time-series sentiment data aggregated by different
    time windows (hourly, daily, etc.) for trend analysis and visualization.
    
    Attributes:
        ts: Timestamp of the aggregation window (part of composite primary key)
        granularity: Time granularity ('hourly', 'daily', 'weekly', etc.) (part of composite primary key)
        raw_value: Raw aggregated sentiment value
        smoothed_value: Smoothed sentiment value (e.g., moving average)
        n_posts: Number of posts included in this aggregation
        n_positive: Number of positive posts in this aggregation
        n_negative: Number of negative posts in this aggregation
        directional_bias: Directional bias score: (n_positive - n_negative) / n_posts
                         Ranges from -1 (all negative) to +1 (all positive)
    """
    
    __tablename__ = "sentiment_indices"
    
    ts = Column(DateTime, primary_key=True, nullable=False)
    granularity = Column(Text, primary_key=True, nullable=False)
    raw_value = Column(Float, nullable=False)
    smoothed_value = Column(Float, nullable=True)
    n_posts = Column(Integer, nullable=False, default=0)
    n_positive = Column(Integer, nullable=False, default=0)
    n_negative = Column(Integer, nullable=False, default=0)
    directional_bias = Column(Float, nullable=True)
    
    def __repr__(self) -> str:
        """Return a string representation of the SentimentIndex for debugging."""
        smoothed_str = f"{self.smoothed_value:.3f}" if self.smoothed_value is not None else "N/A"
        bias_str = f"{self.directional_bias:.3f}" if self.directional_bias is not None else "N/A"
        return (
            f"<SentimentIndex(ts={self.ts}, granularity='{self.granularity}', "
            f"raw={self.raw_value:.3f}, smoothed={smoothed_str}, "
            f"n_posts={self.n_posts}, bias={bias_str})>"
        )


if __name__ == "__main__":
    # Demonstration and testing of the schema models
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    
    print("="*60)
    print("SQLAlchemy Schema Models")
    print("="*60)
    
    # Create an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=True)
    
    # Create all tables
    print("\nCreating tables...")
    Base.metadata.create_all(engine)
    
    # Create a session
    with Session(engine) as session:
        # Test RawItem
        print("\n" + "="*60)
        print("Testing RawItem model")
        print("="*60)
        raw_item = RawItem(
            id="reddit_123456",
            source="reddit",
            ts=datetime(2025, 10, 15, 12, 0, 0),
            title="Bitcoin is going to the moon!",
            text="I think BTC will reach $100k soon because of institutional adoption...",
            url="https://reddit.com/r/bitcoin/comments/123456"
        )
        session.add(raw_item)
        session.commit()
        print(f"Created: {raw_item}")
        
        # Test Price
        print("\n" + "="*60)
        print("Testing Price model")
        print("="*60)
        price = Price(
            ts=datetime(2025, 10, 15, 12, 0, 0),
            price=67500.50,
            volume=28500000000.00
        )
        session.add(price)
        session.commit()
        print(f"Created: {price}")
        
        # Test ScoredItem
        print("\n" + "="*60)
        print("Testing ScoredItem model")
        print("="*60)
        scored_item = ScoredItem(
            id="reddit_123456",
            polarity=0.85,
            probs_json={"positive": 0.85, "neutral": 0.10, "negative": 0.05},
            ts=datetime(2025, 10, 15, 12, 5, 0),
            source="reddit"
        )
        session.add(scored_item)
        session.commit()
        print(f"Created: {scored_item}")
        
        # Test SentimentIndex
        print("\n" + "="*60)
        print("Testing SentimentIndex model")
        print("="*60)
        sentiment_index = SentimentIndex(
            ts=datetime(2025, 10, 15, 12, 0, 0),
            granularity="hourly",
            raw_value=0.65,
            smoothed_value=0.62,
            n_posts=150
        )
        session.add(sentiment_index)
        session.commit()
        print(f"Created: {sentiment_index}")
        
        # Query and display all records
        print("\n" + "="*60)
        print("Querying all records")
        print("="*60)
        
        print(f"\nRawItems: {session.query(RawItem).count()}")
        for item in session.query(RawItem).all():
            print(f"  {item}")
        
        print(f"\nPrices: {session.query(Price).count()}")
        for item in session.query(Price).all():
            print(f"  {item}")
        
        print(f"\nScoredItems: {session.query(ScoredItem).count()}")
        for item in session.query(ScoredItem).all():
            print(f"  {item}")
        
        print(f"\nSentimentIndices: {session.query(SentimentIndex).count()}")
        for item in session.query(SentimentIndex).all():
            print(f"  {item}")
    
    print("\n" + "="*60)
    print("Schema testing complete!")
    print("="*60)
