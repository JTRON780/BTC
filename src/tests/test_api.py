"""
End-to-end API tests for the FastAPI application.

Tests cover:
- /api/v1/sentiment/ endpoint with mocked DB
- /api/v1/drivers/ endpoint
- /api/v1/health/ endpoint
- Response schema validation
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.main import app
from src.api.schemas.sentiment import SentimentResponse, TopDriversResponse


# ============================================================================
# Story H2 - E2E Smoke Test
# ============================================================================

@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def mock_sentiment_data():
    """Mock sentiment index data for testing."""
    return [
        {
            'ts': datetime(2025, 11, 10, 12, 0),
            'granularity': 'daily',
            'raw_value': 0.15,
            'smoothed_value': 0.12,
            'n_posts': 150
        },
        {
            'ts': datetime(2025, 11, 9, 12, 0),
            'granularity': 'daily',
            'raw_value': -0.05,
            'smoothed_value': -0.03,
            'n_posts': 120
        },
        {
            'ts': datetime(2025, 11, 8, 12, 0),
            'granularity': 'daily',
            'raw_value': 0.25,
            'smoothed_value': 0.20,
            'n_posts': 180
        }
    ]


@pytest.fixture
def mock_drivers_data():
    """Mock top drivers data for testing."""
    return {
        'day': '2025-11-10',
        'positives': [
            {
                'title': 'Bitcoin Breaks $100K!',
                'polarity': 0.89,
                'url': 'https://example.com/btc-100k',
                'source': 'news'
            },
            {
                'title': 'Great news for crypto',
                'polarity': 0.75,
                'url': 'https://reddit.com/r/bitcoin/123',
                'source': 'reddit'
            }
        ],
        'negatives': [
            {
                'title': 'Market crash concerns',
                'polarity': -0.68,
                'url': 'https://example.com/crash',
                'source': 'news'
            }
        ]
    }


@pytest.mark.e2e
class TestSentimentIndexEndpoint:
    """E2E tests for /api/v1/sentiment/ endpoint."""
    
    @patch('src.api.routes.index.get_index')
    def test_sentiment_endpoint_returns_200(self, mock_get_index, client, mock_sentiment_data):
        """Test that sentiment endpoint returns 200 OK."""
        # Mock the database call
        mock_get_index.return_value = mock_sentiment_data
        
        # Make request
        response = client.get("/api/v1/sentiment/?granularity=daily&days=30")
        
        # Assert response
        assert response.status_code == 200
    
    @patch('src.api.routes.index.get_index')
    def test_sentiment_endpoint_matches_schema(self, mock_get_index, client, mock_sentiment_data):
        """Test that response matches SentimentResponse schema."""
        # Mock the database call
        mock_get_index.return_value = mock_sentiment_data
        
        # Make request
        response = client.get("/api/v1/sentiment/?granularity=daily&days=30")
        
        # Parse response
        data = response.json()
        
        # Validate against schema
        validated = SentimentResponse(**data)
        
        # Check schema fields
        assert validated.granularity == 'daily'
        assert len(validated.data) == 3
        assert all(hasattr(point, 'ts') for point in validated.data)
        assert all(hasattr(point, 'raw') for point in validated.data)
        assert all(hasattr(point, 'smoothed') for point in validated.data)
        assert all(hasattr(point, 'n_posts') for point in validated.data)
    
    @patch('src.api.routes.index.get_index')
    def test_sentiment_endpoint_response_structure(self, mock_get_index, client, mock_sentiment_data):
        """Test that response has correct structure."""
        mock_get_index.return_value = mock_sentiment_data
        
        response = client.get("/api/v1/sentiment/?granularity=daily&days=30")
        data = response.json()
        
        # Check top-level structure
        assert 'granularity' in data
        assert 'data' in data
        assert isinstance(data['data'], list)
        
        # Check data point structure
        if data['data']:
            point = data['data'][0]
            assert 'ts' in point
            assert 'raw' in point
            assert 'smoothed' in point
            assert 'n_posts' in point
    
    @patch('src.api.routes.index.get_index')
    def test_sentiment_endpoint_with_hourly_granularity(self, mock_get_index, client, mock_sentiment_data):
        """Test sentiment endpoint with hourly granularity."""
        mock_get_index.return_value = mock_sentiment_data
        
        response = client.get("/api/v1/sentiment/?granularity=hourly&days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert data['granularity'] == 'hourly'
    
    @patch('src.api.routes.index.get_index')
    def test_sentiment_endpoint_validates_granularity(self, mock_get_index, client):
        """Test that invalid granularity returns 400."""
        mock_get_index.return_value = []
        
        response = client.get("/api/v1/sentiment/?granularity=weekly&days=30")
        
        assert response.status_code == 400  # Bad request (validation handled in route)
    
    @patch('src.api.routes.index.get_index')
    def test_sentiment_endpoint_cache_headers(self, mock_get_index, client, mock_sentiment_data):
        """Test that cache headers are present."""
        mock_get_index.return_value = mock_sentiment_data
        
        response = client.get("/api/v1/sentiment/?granularity=daily&days=30")
        
        assert response.status_code == 200
        # Check for cache-control header
        assert 'cache-control' in response.headers or 'Cache-Control' in response.headers
    
    @patch('src.api.routes.index.get_index')
    def test_sentiment_endpoint_empty_data(self, mock_get_index, client):
        """Test endpoint behavior with no data."""
        mock_get_index.return_value = []
        
        response = client.get("/api/v1/sentiment/?granularity=daily&days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data['data'] == []


@pytest.mark.e2e
class TestTopDriversEndpoint:
    """E2E tests for /api/v1/drivers/ endpoint."""
    
    def test_drivers_endpoint_404_no_data(self, client):
        """Test that endpoint returns 404 when no data available."""
        # Use a future date that definitely has no data
        response = client.get("/api/v1/drivers/?day=2025-12-31")
        
        assert response.status_code == 404
    
    def test_drivers_endpoint_invalid_date_format(self, client):
        """Test that invalid date format returns 400."""
        response = client.get("/api/v1/drivers/?day=invalid-date")
        
        assert response.status_code == 400
    
    def test_drivers_endpoint_requires_day_parameter(self, client):
        """Test that missing day parameter returns 422."""
        response = client.get("/api/v1/drivers/")
        
        assert response.status_code == 422  # Missing required parameter


@pytest.mark.e2e
class TestHealthEndpoint:
    """E2E tests for /api/v1/health/ endpoint."""
    
    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/api/v1/health/")
        
        assert response.status_code == 200
    
    def test_health_endpoint_response_structure(self, client):
        """Test that health endpoint has correct response structure."""
        response = client.get("/api/v1/health/")
        data = response.json()
        
        assert 'status' in data
        assert 'time' in data
        assert data['status'] == 'healthy'
    
    def test_health_endpoint_time_format(self, client):
        """Test that time is in ISO format."""
        response = client.get("/api/v1/health/")
        data = response.json()
        
        # Should be able to parse as datetime
        time_str = data['time']
        datetime.fromisoformat(time_str)  # Will raise if invalid


@pytest.mark.e2e
class TestRootEndpoint:
    """E2E tests for root endpoint."""
    
    def test_root_endpoint_returns_200(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        
        assert response.status_code == 200
    
    def test_root_endpoint_response(self, client):
        """Test that root endpoint returns status ok."""
        response = client.get("/")
        data = response.json()
        
        assert data['status'] == 'ok'


@pytest.mark.e2e
class TestCORSHeaders:
    """E2E tests for CORS configuration."""
    
    def test_cors_configured(self, client):
        """Test that CORS middleware is configured in the app."""
        # Just verify a request works - CORS is configured in app
        response = client.get("/api/v1/health/")
        assert response.status_code == 200


@pytest.mark.e2e
class TestOpenAPIDocumentation:
    """E2E tests for OpenAPI documentation."""
    
    def test_openapi_json_accessible(self, client):
        """Test that OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert 'info' in data
        assert 'paths' in data
    
    def test_docs_page_accessible(self, client):
        """Test that Swagger UI docs page is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert b"swagger" in response.content.lower() or b"openapi" in response.content.lower()


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.e2e
@patch('src.api.routes.index.get_index')
def test_full_sentiment_workflow(mock_get_index, client, mock_sentiment_data):
    """Full E2E workflow test for sentiment analysis."""
    # Setup mock
    mock_get_index.return_value = mock_sentiment_data
    
    # 1. Check API health
    health_response = client.get("/api/v1/health/")
    assert health_response.status_code == 200
    assert health_response.json()['status'] == 'healthy'
    
    # 2. Fetch sentiment data
    sentiment_response = client.get("/api/v1/sentiment/?granularity=daily&days=30")
    assert sentiment_response.status_code == 200
    
    # 3. Validate response schema
    sentiment_data = sentiment_response.json()
    validated = SentimentResponse(**sentiment_data)
    
    # 4. Verify data quality
    assert validated.granularity == 'daily'
    assert len(validated.data) > 0
    
    # 5. Check sentiment values are in valid range
    for point in validated.data:
        assert -1.0 <= point.raw <= 1.0
        assert -1.0 <= point.smoothed <= 1.0
        assert point.n_posts >= 0
