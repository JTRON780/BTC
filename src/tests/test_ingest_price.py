"""
Unit tests for price ingestion helpers.
"""

from datetime import datetime

import pytest

from src.ingest.price import fetch_current_price, fetch_price_snapshot, backfill_prices


class FakeResponse:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


@pytest.mark.fast
def test_fetch_current_price_parses_response(monkeypatch):
    monkeypatch.setenv("COINGECKO_BASE", "https://api.coingecko.com/api/v3")

    payload = {
        "bitcoin": {
            "usd": 50000,
            "usd_24h_change": 1.25,
            "usd_24h_vol": 123456789,
            "last_updated_at": 1700000000
        }
    }

    def fake_get(_url, params=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr("src.ingest.price.requests.get", fake_get)

    result = fetch_current_price()
    assert result["price"] == 50000.0
    assert result["price_change_24h"] == 1.25
    assert result["volume_24h"] == 123456789.0
    assert isinstance(result["last_updated"], datetime)


@pytest.mark.fast
def test_fetch_price_snapshot_parses_response(monkeypatch):
    monkeypatch.setenv("COINGECKO_BASE", "https://api.coingecko.com/api/v3")

    payload = {
        "bitcoin": {
            "usd": 51000,
            "usd_24h_vol": 987654321
        }
    }

    def fake_get(_url, params=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr("src.ingest.price.requests.get", fake_get)

    result = fetch_price_snapshot()
    assert result["price"] == 51000.0
    assert result["volume"] == 987654321.0
    assert isinstance(result["ts"], datetime)


@pytest.mark.fast
def test_backfill_prices_parses_history(monkeypatch):
    monkeypatch.setenv("COINGECKO_BASE", "https://api.coingecko.com/api/v3")

    payload = {
        "prices": [
            [1700000000000, 40000.0],
            [1700003600000, 40500.0]
        ],
        "total_volumes": [
            [1700000000000, 1000.0],
            [1700003600000, 1500.0]
        ]
    }

    def fake_get(_url, params=None, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr("src.ingest.price.requests.get", fake_get)

    results = backfill_prices(hours=2)
    assert len(results) == 2
    assert results[0]["price"] == 40000.0
    assert results[0]["volume"] == 1000.0
