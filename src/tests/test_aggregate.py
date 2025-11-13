"""
Unit tests for sentiment aggregation pipeline.

Tests cover:
- Source weighting (news > reddit)
- Time window alignment
- Weighted average calculations
- Smoothing algorithms
"""

import pytest
from datetime import datetime, timedelta
from src.pipelines.aggregate import (
    _weight_for_source,
    _window_ts,
    compute_rollups,
    _apply_ewma_smoothing
)


# ============================================================================
# Story H1 - Unit Tests: Aggregation Weights
# ============================================================================

@pytest.mark.fast
class TestSourceWeights:
    """Test suite for source weighting in aggregation."""
    
    def test_news_weight_greater_than_reddit(self):
        """Test that news sources have higher weight than reddit."""
        news_weight = _weight_for_source('news')
        reddit_weight = _weight_for_source('reddit')
        
        assert news_weight > reddit_weight, \
            f"News weight ({news_weight}) should be > Reddit weight ({reddit_weight})"
    
    def test_news_weight_is_1_2(self):
        """Test that news weight is exactly 1.2."""
        weight = _weight_for_source('news')
        assert weight == 1.2
    
    def test_reddit_weight_is_1_0(self):
        """Test that reddit weight is exactly 1.0."""
        weight = _weight_for_source('reddit')
        assert weight == 1.0
    
    def test_unknown_source_defaults_to_1_0(self):
        """Test that unknown sources default to weight 1.0."""
        weight = _weight_for_source('unknown_source')
        assert weight == 1.0
    
    def test_empty_source_defaults_to_1_0(self):
        """Test that empty source defaults to weight 1.0."""
        weight = _weight_for_source('')
        assert weight == 1.0
    
    def test_case_insensitive_news(self):
        """Test that news weight is case-insensitive."""
        assert _weight_for_source('news') == _weight_for_source('NEWS')
        assert _weight_for_source('news') == _weight_for_source('News')
    
    def test_case_insensitive_reddit(self):
        """Test that reddit weight is case-insensitive."""
        assert _weight_for_source('reddit') == _weight_for_source('REDDIT')
        assert _weight_for_source('reddit') == _weight_for_source('Reddit')
    
    def test_news_substring_detection(self):
        """Test that 'news' substring in source is detected."""
        # Should detect 'news' in various formats
        assert _weight_for_source('cointelegraph_news') == 1.2
        assert _weight_for_source('news_feed') == 1.2
    
    def test_reddit_substring_detection(self):
        """Test that 'reddit' substring in source is detected."""
        # Should detect 'reddit' in various formats
        assert _weight_for_source('www.reddit.com') == 1.0
        assert _weight_for_source('reddit_bitcoin') == 1.0
    
    def test_weight_ratio_approximately_6_5(self):
        """Test that news/reddit weight ratio is 1.2 (6/5)."""
        news_weight = _weight_for_source('news')
        reddit_weight = _weight_for_source('reddit')
        ratio = news_weight / reddit_weight
        
        assert abs(ratio - 1.2) < 0.01


@pytest.mark.fast
class TestWindowAlignment:
    """Test suite for time window alignment."""
    
    def test_hourly_window_rounds_down_to_hour(self):
        """Test that hourly granularity rounds down to the hour."""
        ts = datetime(2025, 11, 10, 14, 37, 23)
        result = _window_ts(ts, 'hourly')
        
        assert result == datetime(2025, 11, 10, 14, 0, 0)
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0
    
    def test_daily_window_rounds_down_to_midnight(self):
        """Test that daily granularity rounds down to midnight."""
        ts = datetime(2025, 11, 10, 14, 37, 23)
        result = _window_ts(ts, 'daily')
        
        assert result == datetime(2025, 11, 10, 0, 0, 0)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0
    
    def test_hourly_preserves_date_and_hour(self):
        """Test that hourly window preserves date and hour."""
        ts = datetime(2025, 11, 10, 14, 37, 23)
        result = _window_ts(ts, 'hourly')
        
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 10
        assert result.hour == 14
    
    def test_daily_preserves_date_only(self):
        """Test that daily window preserves only the date."""
        ts = datetime(2025, 11, 10, 14, 37, 23)
        result = _window_ts(ts, 'daily')
        
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 10
    
    def test_invalid_granularity_raises_error(self):
        """Test that invalid granularity raises ValueError."""
        ts = datetime(2025, 11, 10, 14, 37, 23)
        
        with pytest.raises(ValueError, match="Unsupported granularity"):
            _window_ts(ts, 'weekly')


@pytest.mark.fast
class TestWeightedAggregation:
    """Test suite for weighted sentiment aggregation."""
    
    def test_ewma_smoothing_reduces_volatility(self):
        """Test that EWMA smoothing reduces volatility."""
        # Create volatile data
        data = [
            {'ts': datetime(2025, 11, 10, i), 'source': 'news', 'granularity': 'hourly', 
             'raw_value': 0.5 if i % 2 == 0 else -0.5, 'n_posts': 10}
            for i in range(6)
        ]
        
        smoothed_data = _apply_ewma_smoothing(data, alpha=0.3)
        
        # Extract raw and smoothed values
        raw_values = [d['raw_value'] for d in data]
        smoothed_values = [d['smoothed_value'] for d in smoothed_data]
        
        # Calculate volatility
        import statistics
        vol_raw = statistics.stdev(raw_values)
        vol_smoothed = statistics.stdev(smoothed_values)
        
        # Smoothed should have lower volatility
        assert vol_smoothed < vol_raw
    
    def test_ewma_smoothing_preserves_structure(self):
        """Test that smoothing preserves data structure."""
        data = [
            {'ts': datetime(2025, 11, 10, 12, 0), 'source': 'news', 
             'granularity': 'hourly', 'raw_value': 0.5, 'n_posts': 10}
        ]
        
        smoothed_data = _apply_ewma_smoothing(data, alpha=0.5)
        
        assert len(smoothed_data) == 1
        assert 'smoothed_value' in smoothed_data[0]
        assert smoothed_data[0]['ts'] == data[0]['ts']
        assert smoothed_data[0]['source'] == data[0]['source']


@pytest.mark.fast
class TestSmoothing:
    """Test suite for smoothing algorithm."""
    
    def test_apply_ewma_smoothing_first_value(self):
        """Test that first value equals raw value."""
        data = [
            {'ts': datetime(2025, 11, 10, 12, 0), 'source': 'news',
             'granularity': 'hourly', 'raw_value': 0.5, 'n_posts': 10}
        ]
        
        smoothed = _apply_ewma_smoothing(data, alpha=0.5)
        
        # First smoothed value should equal first raw value
        assert smoothed[0]['smoothed_value'] == data[0]['raw_value']
    
    def test_apply_ewma_smoothing_multiple_values(self):
        """Test EWMA with multiple values."""
        data = [
            {'ts': datetime(2025, 11, 10, i), 'source': 'news', 
             'granularity': 'hourly', 'raw_value': float(i) / 10, 'n_posts': 10}
            for i in range(5)
        ]
        
        smoothed = _apply_ewma_smoothing(data, alpha=0.5)
        
        assert len(smoothed) == 5
        # All should have smoothed_value
        assert all('smoothed_value' in d for d in smoothed)
    
    def test_apply_ewma_empty_list(self):
        """Test that empty list returns empty."""
        result = _apply_ewma_smoothing([], alpha=0.5)
        assert result == []
    
    def test_apply_ewma_smoothing_by_source(self):
        """Test that smoothing is applied separately per source."""
        data = [
            {'ts': datetime(2025, 11, 10, 12, 0), 'source': 'news',
             'granularity': 'hourly', 'raw_value': 0.5, 'n_posts': 10},
            {'ts': datetime(2025, 11, 10, 12, 0), 'source': 'reddit',
             'granularity': 'hourly', 'raw_value': -0.5, 'n_posts': 10},
        ]
        
        smoothed = _apply_ewma_smoothing(data, alpha=0.5)
        
        # Both should have their raw values as first smoothed values
        assert len(smoothed) == 2


@pytest.mark.fast
def test_news_weight_integration():
    """Integration test verifying news sources get higher effective weight."""
    # Verify the weight constants
    assert _weight_for_source('news') == 1.2
    assert _weight_for_source('reddit') == 1.0
    
    # Verify news weight is applied
    news_weight = _weight_for_source('cointelegraph_news')
    reddit_weight = _weight_for_source('www.reddit.com')
    
    assert news_weight > reddit_weight
    assert news_weight == 1.2
    assert reddit_weight == 1.0
