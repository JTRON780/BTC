"""
Data storage and repository layer for the BTC sentiment analysis application.

This module provides:
- schemas: SQLAlchemy ORM models for database tables
- stores: Repository pattern implementations for data access
"""

from src.data.schemas import Base, RawItem, Price, ScoredItem, SentimentIndex
from src.data.stores import (
    init_db,
    get_engine,
    upsert_raw_items,
    get_recent_raw_items,
    save_scores,
    save_prices,
    get_prices,
    save_sentiment_indices,
    get_index,
)

__all__ = [
    # Schema models
    "Base",
    "RawItem",
    "Price",
    "ScoredItem",
    "SentimentIndex",
    # Repository functions
    "init_db",
    "get_engine",
    "upsert_raw_items",
    "get_recent_raw_items",
    "save_scores",
    "save_prices",
    "get_prices",
    "save_sentiment_indices",
    "get_index",
]
