"""
Unit tests for ingest modules (news and reddit).
"""

from types import SimpleNamespace
from datetime import datetime
import time

import pytest

from src.ingest.news import fetch_news_feeds
from src.ingest.reddit import fetch_reddit_feeds


class Entry(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


@pytest.mark.fast
def test_fetch_news_feeds_normalizes_entries(monkeypatch):
    published = time.gmtime()
    entry = SimpleNamespace(
        link="https://example.com/article",
        title="Bitcoin hits new high",
        summary="Bitcoin news summary",
        published_parsed=published
    )
    parsed_feed = SimpleNamespace(bozo=False, entries=[entry])

    def fake_parse(_url):
        return parsed_feed

    monkeypatch.setattr("src.ingest.news.feedparser.parse", fake_parse)

    items = fetch_news_feeds(["https://example.com/rss"])

    assert len(items) == 1
    item = items[0]
    assert item["id"].startswith("news_")
    assert item["title"] == "Bitcoin hits new high"
    assert item["url"] == "https://example.com/article"
    assert item["text"] == "Bitcoin news summary"
    assert isinstance(item["ts"], datetime)


@pytest.mark.fast
def test_fetch_reddit_feeds_filters_non_bitcoin(monkeypatch):
    published = time.gmtime()
    bitcoin_entry = Entry(
        link="https://www.reddit.com/r/bitcoin/comments/abc123/bitcoin_news",
        title="Bitcoin rally",
        summary="btc is moving",
        published_parsed=published
    )
    other_entry = Entry(
        link="https://www.reddit.com/r/bitcoin/comments/def456/other_topic",
        title="Totally unrelated",
        summary="nothing about it",
        published_parsed=published
    )
    parsed_feed = SimpleNamespace(bozo=False, entries=[bitcoin_entry, other_entry])

    class FakeResponse:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

    def fake_get(_url, headers=None, timeout=None):
        return FakeResponse(b"<rss></rss>")

    def fake_parse(_content):
        return parsed_feed

    monkeypatch.setattr("src.ingest.reddit.requests.get", fake_get)
    monkeypatch.setattr("src.ingest.reddit.feedparser.parse", fake_parse)

    items = fetch_reddit_feeds(["bitcoin"])

    assert len(items) == 1
    assert "bitcoin" in items[0]["title"].lower()

def test_placeholder():
    assert True
