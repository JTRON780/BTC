"""
Index router for the BTC sentiment analysis API.

Provides sentiment index data endpoints for time series analysis.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Response
from hashlib import md5
import json

from src.core import get_logger, get_settings
from src.data import get_index, init_db
from src.api.schemas.sentiment import SentimentIndexPoint, SentimentResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=SentimentResponse)
async def get_sentiment_indices(
    response: Response,
    granularity: str = Query("daily", description="Time granularity (hourly, daily)"),
    days: int = Query(7, description="Number of days to look back", ge=1, le=365),
    source: Optional[str] = Query(None, description="Filter by data source")
) -> SentimentResponse:
    """
    Get sentiment indices for the specified time range and granularity.
    
    This endpoint retrieves aggregated sentiment data with both raw and EWMA-smoothed
    values. Results are cached for improved performance.
    
    Args:
        response: FastAPI Response object for setting headers
        granularity: Time granularity ('hourly', 'daily')
        days: Number of days to look back (1-365)
        source: Optional source filter (currently not supported in schema)
        
    Returns:
        SentimentResponse with list of sentiment index data points
        
    Example:
        GET /api/v1/sentiment/?granularity=hourly&days=7
        
    Cache Headers:
        Cache-Control: Caching policy based on granularity
        ETag: Content hash for conditional requests
    """
    try:
        # Validate granularity
        if granularity not in ("hourly", "daily"):
            raise HTTPException(
                status_code=400, 
                detail="Granularity must be 'hourly' or 'daily'"
            )
        
        # Initialize database if needed
        config = get_settings()
        init_db(config.DB_URL)
        
        logger.info(f"Querying database with granularity={granularity}, days={days}")
        logger.info(f"Database URL: {config.DB_URL}")
        
        # Get indices from database
        indices = get_index(granularity=granularity, days=days)
        
        logger.info(f"Found {len(indices)} indices")
        if len(indices) == 0:
            logger.warning("No data returned from database - checking if DB has any records")
            # Quick diagnostic query
            try:
                from src.data.stores import get_engine
                from sqlalchemy import text
                engine = get_engine()
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM sentiment_indices")).scalar()
                    logger.info(f"Total records in sentiment_indices table: {result}")
            except Exception as e:
                logger.error(f"Error checking database: {e}")
        
        # Apply source filter if provided
        # Note: Current schema doesn't have source field in sentiment_indices
        # This would need to be added to the schema for source filtering
        if source:
            logger.warning(
                "Source filtering requested but not supported in current schema",
                extra={'source': source}
            )
        
        # Convert to Pydantic models
        data_points = []
        for idx in indices:
            point = SentimentIndexPoint(
                ts=idx['ts'],
                raw=idx['raw_value'],
                smoothed=idx.get('smoothed_value', idx['raw_value']),  # Fallback to raw if no smoothed
                n_posts=idx['n_posts']
            )
            data_points.append(point)
        
        # Create response
        sentiment_response = SentimentResponse(
            granularity=granularity,
            data=data_points
        )
        
        # Set cache headers
        # Hourly data: cache for 5 minutes (data updates frequently)
        # Daily data: cache for 30 minutes (more stable)
        cache_duration = 300 if granularity == "hourly" else 1800
        response.headers["Cache-Control"] = f"public, max-age={cache_duration}"
        
        # Generate ETag based on content for conditional requests
        content_hash = md5(
            sentiment_response.model_dump_json().encode('utf-8')
        ).hexdigest()
        response.headers["ETag"] = f'"{content_hash}"'
        
        # Add Last-Modified header if we have data
        if data_points:
            latest_ts = max(point.ts for point in data_points)
            response.headers["Last-Modified"] = latest_ts.strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        
        logger.info(
            f"Retrieved sentiment indices",
            extra={
                'count': len(indices),
                'granularity': granularity,
                'days': days,
                'source': source,
                'cache_duration': cache_duration
            }
        )
        
        return sentiment_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving sentiment indices", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/latest", response_model=SentimentResponse)
async def get_latest_sentiment() -> SentimentResponse:
    """
    Get the most recent sentiment reading.
    
    Returns:
        SentimentResponse with the latest sentiment index data point
    """
    try:
        config = get_settings()
        init_db(config.DB_URL)
        
        # Get latest daily reading
        indices = get_index(granularity="daily", days=1)
        
        if not indices:
            # Try hourly if no daily data
            indices = get_index(granularity="hourly", days=1)
        
        if not indices:
            # Return empty response if no data
            return SentimentResponse(
                granularity="daily",
                data=[]
            )
        
        # Get the latest index
        latest = max(indices, key=lambda x: x['ts'])
        
        # Convert to Pydantic model
        latest_point = SentimentIndexPoint(
            ts=latest['ts'],
            raw=latest['raw_value'],
            smoothed=latest.get('smoothed_value', latest['raw_value']),
            n_posts=latest['n_posts']
        )
        
        return SentimentResponse(
            granularity="latest",
            data=[latest_point]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving latest sentiment", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")
