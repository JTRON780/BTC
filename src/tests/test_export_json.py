"""
Unit tests for JSON export pipeline.
"""

import json
from datetime import datetime

import pytest

from src.data import init_db, save_sentiment_indices, save_scores, upsert_raw_items, get_engine
from src.pipelines.export_json import (
    export_sentiment_indices,
    export_top_drivers,
    export_current_price,
)


@pytest.mark.fast
def test_export_sentiment_indices_writes_file(tmp_path, monkeypatch):
    db_path = tmp_path / "export.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DB_URL", db_url)
    init_db(db_url)

    ts = datetime.utcnow()
    save_sentiment_indices([
        {
            "ts": ts,
            "granularity": "daily",
            "raw_value": 0.2,
            "smoothed_value": 0.15,
            "n_posts": 5,
            "n_positive": 3,
            "n_negative": 2,
            "directional_bias": 0.2
        }
    ])

    export_sentiment_indices(tmp_path, granularity="daily", days=1)

    output_file = tmp_path / "sentiment_daily.json"
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["granularity"] == "daily"
    assert len(data["data"]) == 1
    assert data["data"][0]["raw"] == 0.2

    get_engine().dispose()


@pytest.mark.fast
def test_export_top_drivers_writes_file(tmp_path, monkeypatch):
    db_path = tmp_path / "drivers.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DB_URL", db_url)
    init_db(db_url)

    ts = datetime.utcnow()
    upsert_raw_items([
        {
            "id": "item_1",
            "source": "news",
            "ts": ts,
            "title": "Bitcoin update",
            "text": "btc moves",
            "url": "https://example.com/item"
        }
    ])
    save_scores([
        {
            "id": "item_1",
            "polarity": 0.6,
            "probs_json": {"pos": 0.7, "neu": 0.2, "neg": 0.1},
            "ts": ts,
            "source": "news"
        }
    ])

    export_top_drivers(tmp_path, days=1)

    drivers_dir = tmp_path / "drivers"
    files = list(drivers_dir.glob("*.json"))
    assert files

    data = json.loads(files[0].read_text())
    assert "positives" in data
    assert len(data["positives"]) == 1

    get_engine().dispose()


@pytest.mark.fast
def test_export_current_price_writes_file(tmp_path, monkeypatch):
    def fake_price():
        return {
            "price": 50000.0,
            "price_change_24h": 1.0,
            "volume_24h": 123.0,
            "last_updated": datetime(2025, 11, 10, 12, 0, 0)
        }

    monkeypatch.setattr("src.pipelines.export_json.fetch_current_price", fake_price)

    export_current_price(tmp_path)
    output_file = tmp_path / "price.json"
    assert output_file.exists()
