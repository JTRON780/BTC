"""
Smoke tests for pipeline integration with a temporary SQLite database.
"""

from datetime import datetime

import pytest

from src.core import get_settings
from src.data import get_index, get_engine
from src.data.schemas import SentimentIndex
from sqlalchemy import select, func

from src.pipelines.aggregate import run_aggregation
from src.pipelines.collect import run_collect
from src.pipelines.score import run_scoring_pipeline


class DummyModel:
    def predict(self, batch):
        return [{"neg": 0.1, "neu": 0.2, "pos": 0.7} for _ in batch]


@pytest.mark.integration
def test_pipeline_smoke(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    monkeypatch.setenv("DB_URL", db_url)
    monkeypatch.setenv("NEWS_FEEDS", "https://example.com/rss")
    monkeypatch.setenv("REDDIT_FEEDS", "bitcoin")
    monkeypatch.setenv("COINGECKO_BASE", "https://api.coingecko.com/api/v3")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost")
    get_settings.cache_clear()

    now = datetime.utcnow()
    news_items = [
        {
            "id": "news_1",
            "source": "news",
            "ts": now,
            "title": "Bitcoin rally",
            "text": "bitcoin is up",
            "url": "https://example.com/news"
        }
    ]
    reddit_items = [
        {
            "id": "reddit_1",
            "source": "reddit",
            "ts": now,
            "title": "BTC discussion",
            "text": "bitcoin on reddit",
            "url": "https://reddit.com/r/bitcoin/1"
        }
    ]

    def fake_fetch_news(_feeds):
        return news_items

    def fake_fetch_reddit(_feeds):
        return reddit_items

    def fake_snapshot():
        return {"ts": now, "price": 50000.0, "volume": 1.0}

    monkeypatch.setattr("src.pipelines.collect.fetch_news_feeds", fake_fetch_news)
    monkeypatch.setattr("src.pipelines.collect.fetch_reddit_feeds", fake_fetch_reddit)
    monkeypatch.setattr("src.pipelines.collect.fetch_price_snapshot", fake_snapshot)
    monkeypatch.setattr("src.pipelines.score.SentimentModel", lambda: DummyModel())

    collect_stats = run_collect()
    assert collect_stats["news"] == 1
    assert collect_stats["reddit"] == 1
    assert collect_stats["price_snapshots"] == 1

    score_stats = run_scoring_pipeline(since_hours=24)
    assert score_stats["items_saved"] == 2

    agg_stats = run_aggregation(granularity="hourly", days=1)
    assert agg_stats["saved"] > 0

    indices = get_index(granularity="hourly", days=1)
    assert len(indices) > 0

    engine = get_engine()
    with engine.connect() as conn:
        count = conn.execute(
            select(func.count()).select_from(SentimentIndex)
        ).scalar()
    assert count and count > 0
