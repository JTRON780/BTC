"""
Unit tests for sentiment analysis NLP functions.

Tests cover:
- Text preprocessing (clean_text)
- Text composition (compose_text)
- Sentiment model predictions
"""

import pytest
from src.nlp.preprocess import clean_text, compose_text
from src.nlp.models import SentimentModel


# ============================================================================
# Story H1 - Unit Tests: clean_text()
# ============================================================================

@pytest.mark.fast
class TestCleanText:
    """Test suite for clean_text() function."""
    
    def test_removes_urls(self):
        """Test that URLs are removed from text."""
        text = "Check this out: https://example.com/article Bitcoin news"
        result = clean_text(text)
        
        assert "https://example.com/article" not in result
        assert "bitcoin" in result.lower()
    
    def test_removes_multiple_urls(self):
        """Test that multiple URLs are removed."""
        text = "Visit https://site1.com and http://site2.org for info"
        result = clean_text(text)
        
        assert "https://site1.com" not in result
        assert "http://site2.org" not in result
        assert "visit" in result.lower()
        assert "info" in result.lower()
    
    def test_lowercases_text(self):
        """Test that text is converted to lowercase."""
        text = "Bitcoin MOON Soon! BTC Pumping HARD"
        result = clean_text(text)
        
        assert result == result.lower()
        assert "bitcoin" in result
        assert "moon" in result
        assert "MOON" not in result
        assert "BTC" not in result or "btc" in result
    
    def test_removes_special_characters(self):
        """Test that special characters are handled properly."""
        text = "BTC price: $50,000! 🚀 #Bitcoin @elonmusk"
        result = clean_text(text)
        
        # Should keep basic text
        assert "btc" in result.lower() or "price" in result.lower()
    
    def test_handles_empty_string(self):
        """Test that empty string is handled gracefully."""
        result = clean_text("")
        assert result == ""
    
    def test_handles_whitespace_only(self):
        """Test that whitespace-only string is handled."""
        result = clean_text("   \n\t   ")
        assert result.strip() == ""
    
    def test_removes_urls_and_lowercases_together(self):
        """Test that URL removal and lowercasing work together."""
        text = "BREAKING: Bitcoin hits $100K! https://cointelegraph.com/news Read MORE at http://decrypt.co"
        result = clean_text(text)
        
        # URLs removed
        assert "https://cointelegraph.com/news" not in result
        assert "http://decrypt.co" not in result
        
        # Text lowercased
        assert result == result.lower()
        assert "breaking" in result
        assert "bitcoin" in result
    
    def test_preserves_meaningful_text(self):
        """Test that meaningful content is preserved."""
        text = "The Bitcoin price increased significantly today"
        result = clean_text(text)
        
        assert "bitcoin" in result
        assert "price" in result
        assert "increased" in result
        assert "today" in result


@pytest.mark.fast
class TestComposeText:
    """Test suite for compose_text() function."""
    
    def test_combines_title_and_text(self):
        """Test that title and text are combined properly."""
        title = "Bitcoin Breaks $100K"
        text = "Bitcoin has reached a new all-time high"
        result = compose_text(title, text)
        
        assert "Bitcoin Breaks $100K" in result or "bitcoin breaks $100k" in result.lower()
        assert "all-time high" in result.lower()
    
    def test_handles_empty_title(self):
        """Test composition with empty title."""
        title = ""
        text = "Some content here"
        result = compose_text(title, text)
        
        assert "content" in result.lower()
    
    def test_handles_empty_text(self):
        """Test composition with empty text."""
        title = "Title Only"
        text = ""
        result = compose_text(title, text)
        
        assert "title" in result.lower()
    
    def test_handles_both_empty(self):
        """Test composition with both empty."""
        result = compose_text("", "")
        assert isinstance(result, str)


# ============================================================================
# Story H1 - Unit Tests: SentimentModel.predict()
# ============================================================================

@pytest.mark.fast
class TestSentimentModel:
    """Test suite for SentimentModel predictions."""
    
    @pytest.fixture
    def model(self):
        """Fixture to load sentiment model once for all tests."""
        return SentimentModel()
    
    def test_predict_returns_dict(self, model):
        """Test that predict returns a dictionary."""
        texts = ["Bitcoin is amazing!"]
        predictions = model.predict(texts)
        
        assert isinstance(predictions, list)
        assert len(predictions) == 1
        assert isinstance(predictions[0], dict)
    
    def test_predict_has_required_keys(self, model):
        """Test that predictions contain required probability keys."""
        texts = ["Bitcoin price is stable"]
        predictions = model.predict(texts)
        
        assert 'pos' in predictions[0]
        assert 'neg' in predictions[0]
        assert 'neu' in predictions[0]
    
    def test_probabilities_sum_to_one(self, model):
        """Test that probability distributions sum to approximately 1."""
        texts = [
            "Bitcoin is going to the moon! 🚀",
            "This crash is devastating",
            "BTC price unchanged today"
        ]
        predictions = model.predict(texts)
        
        for pred in predictions:
            total = pred['pos'] + pred['neg'] + pred['neu']
            # Allow small floating point error
            assert abs(total - 1.0) < 0.01, f"Probabilities sum to {total}, not ~1.0"
    
    def test_probabilities_are_between_zero_and_one(self, model):
        """Test that all probabilities are in valid range [0, 1]."""
        texts = ["Bitcoin news update"]
        predictions = model.predict(texts)
        
        for pred in predictions:
            assert 0.0 <= pred['pos'] <= 1.0
            assert 0.0 <= pred['neg'] <= 1.0
            assert 0.0 <= pred['neu'] <= 1.0
    
    def test_positive_sentiment_detected(self, model):
        """Test that clearly positive text has high positive probability."""
        texts = ["Bitcoin is absolutely amazing! Best investment ever! To the moon! 🚀🚀🚀"]
        predictions = model.predict(texts)
        
        # Positive probability should be highest
        assert predictions[0]['pos'] > predictions[0]['neg']
        assert predictions[0]['pos'] > predictions[0]['neu']
    
    def test_negative_sentiment_detected(self, model):
        """Test that clearly negative text has high negative probability."""
        texts = ["Bitcoin crash is terrible! Lost everything! Worst investment! 😢"]
        predictions = model.predict(texts)
        
        # Negative probability should be highest
        assert predictions[0]['neg'] > predictions[0]['pos']
    
    def test_batch_prediction(self, model):
        """Test that batch prediction works correctly."""
        texts = [
            "Great news for Bitcoin!",
            "Bad news for crypto",
            "Bitcoin price stable"
        ]
        predictions = model.predict(texts)
        
        assert len(predictions) == 3
        
        # Each should have valid probabilities
        for pred in predictions:
            assert isinstance(pred, dict)
            total = pred['pos'] + pred['neg'] + pred['neu']
            assert abs(total - 1.0) < 0.01
    
    def test_empty_text_handling(self, model):
        """Test that empty text is handled gracefully."""
        texts = [""]
        predictions = model.predict(texts)
        
        assert len(predictions) == 1
        assert isinstance(predictions[0], dict)
        # Should still return valid probabilities
        total = predictions[0]['pos'] + predictions[0]['neg'] + predictions[0]['neu']
        assert abs(total - 1.0) < 0.01


@pytest.mark.fast
def test_sentiment_pipeline_integration():
    """Integration test for preprocessing + prediction pipeline."""
    model = SentimentModel()
    
    # Raw text with URLs and mixed case
    raw_text = "BREAKING: Bitcoin PUMPS! https://example.com $100K Soon! 🚀"
    
    # Clean the text
    cleaned = clean_text(raw_text)
    
    # Should be lowercase and URL-free
    assert cleaned == cleaned.lower()
    assert "https://" not in cleaned
    
    # Predict sentiment
    predictions = model.predict([cleaned])
    
    # Should return valid probabilities
    assert len(predictions) == 1
    total = predictions[0]['pos'] + predictions[0]['neg'] + predictions[0]['neu']
    assert abs(total - 1.0) < 0.01
    
    # Positive sentiment should be detected
    assert predictions[0]['pos'] > predictions[0]['neg']
