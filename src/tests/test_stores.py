"""
Unit tests for data store repository helpers.
"""

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.data import init_db, save_sentiment_indices, get_engine
from src.data.schemas import SentimentIndex


@pytest.mark.fast
def test_save_sentiment_indices_updates_fields(tmp_path):
    db_path = tmp_path / "stores.db"
    db_url = f"sqlite:///{db_path}"
    init_db(db_url)

    ts = datetime(2025, 11, 10, 12, 0, 0)
    initial = [
        {
            "ts": ts,
            "granularity": "hourly",
            "raw_value": 0.1,
            "smoothed_value": 0.1,
            "n_posts": 10,
            "n_positive": 7,
            "n_negative": 3,
            "directional_bias": 0.4
        }
    ]

    updated = [
        {
            "ts": ts,
            "granularity": "hourly",
            "raw_value": 0.2,
            "smoothed_value": 0.15,
            "n_posts": 12,
            "n_positive": 8,
            "n_negative": 4,
            "directional_bias": 0.33
        }
    ]

    save_sentiment_indices(initial)
    save_sentiment_indices(updated)

    engine = get_engine()
    with Session(engine) as session:
        stmt = select(SentimentIndex).where(
            SentimentIndex.ts == ts,
            SentimentIndex.granularity == "hourly"
        )
        row = session.execute(stmt).scalar_one()

    assert row.raw_value == 0.2
    assert row.smoothed_value == 0.15
    assert row.n_posts == 12
    assert row.n_positive == 8
    assert row.n_negative == 4
    assert abs(row.directional_bias - 0.33) < 0.0001
