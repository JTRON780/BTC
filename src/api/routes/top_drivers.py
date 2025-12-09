"""
Top drivers router for the BTC sentiment analysis API.

Provides endpoints for sentiment trend analysis and driver identification.
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, cast
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from src.core import get_logger, get_settings
from src.data import get_engine, init_db, ScoredItem, get_recent_raw_items
from src.api.schemas.sentiment import TopDriverItem, TopDriversResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=TopDriversResponse)
async def get_top_drivers(
    day: str = Query(..., description="Target date in YYYY-MM-DD format"),
    limit: int = Query(20, description="Number of top drivers to return per sentiment (positive/negative)", ge=1, le=100)
) -> TopDriversResponse:
    """
    Get top positive and negative sentiment drivers for a specific day.
    
    This endpoint retrieves the most influential positive and negative sentiment
    items for a given day, helping identify what content drove market sentiment.
    
    Args:
        day: Target date in YYYY-MM-DD format (required)
        limit: Number of drivers per sentiment type (default: 20, max: 100)
        
    Returns:
        TopDriversResponse with top positive and top negative drivers
        
    Raises:
        400: Invalid date format
        404: No data available for the specified date
        500: Internal server error
        
    Example:
        GET /api/v1/top_drivers?day=2025-11-04&limit=20
    """
    try:
        # Parse the date parameter
        try:
            parsed_date = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-04)"
            )
        
        # Calculate time range for the day
        start_time = datetime.combine(parsed_date, datetime.min.time())
        end_time = datetime.combine(parsed_date, datetime.max.time())
        
        # Initialize database
        config = get_settings()
        init_db(config.DB_URL)
        engine = get_engine()
        
        # Query scored items for the day
        with Session(engine) as session:
            # Get top positive drivers
            positive_stmt = (
                select(ScoredItem)
                .where(ScoredItem.ts >= start_time)
                .where(ScoredItem.ts <= end_time)
                .where(ScoredItem.polarity > 0)
                .order_by(desc(ScoredItem.polarity))
                .limit(limit)
            )
            positive_results = session.execute(positive_stmt).scalars().all()
            
            # Get top negative drivers
            negative_stmt = (
                select(ScoredItem)
                .where(ScoredItem.ts >= start_time)
                .where(ScoredItem.ts <= end_time)
                .where(ScoredItem.polarity < 0)
                .order_by(ScoredItem.polarity)  # Ascending to get most negative first
                .limit(limit)
            )
            negative_results = session.execute(negative_stmt).scalars().all()
        
        # Check if we have any data for this day
        if not positive_results and not negative_results:
            logger.info(
                f"No sentiment data found for date",
                extra={'date': str(parsed_date)}
            )
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment data available for {parsed_date}"
            )
        
        # Fetch raw items for titles and URLs
        raw_items_map = {}
        try:
            # Calculate hours to look back from the target date
            days_ago = (date.today() - parsed_date).days
            hours_to_fetch = max(24, (days_ago + 1) * 24)  # At least 24 hours, or more for older dates
            
            raw_items = get_recent_raw_items(hours=min(hours_to_fetch, 168))  # Cap at 7 days
            raw_items_map = {item['id']: item for item in raw_items}
        except Exception as e:
            logger.warning(
                f"Could not fetch raw items for metadata",
                extra={'error': str(e), 'date': str(parsed_date)}
            )
        
        # Convert to TopDriverItem models
        def create_driver_item(scored_item) -> TopDriverItem:
            """Helper function to create TopDriverItem from ScoredItem."""
            item_id = cast(str, scored_item.id)
            raw_item = raw_items_map.get(item_id, {})
            
            # Use title from raw item or construct a fallback
            title = raw_item.get('title', f'Item {item_id[:8]}...')
            
            return TopDriverItem(
                title=title,
                polarity=float(cast(float, scored_item.polarity)),
                url=raw_item.get('url', ''),
                source=cast(str, scored_item.source)
            )
        
        # Create response
        positives = [create_driver_item(item) for item in positive_results]
        negatives = [create_driver_item(item) for item in negative_results]
        
        logger.info(
            f"Retrieved top drivers for date",
            extra={
                'date': str(parsed_date),
                'positives_count': len(positives),
                'negatives_count': len(negatives)
            }
        )
        
        return TopDriversResponse(
            day=parsed_date,
            positives=positives,
            negatives=negatives
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving top drivers",
            extra={'error': str(e), 'day': day}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sentiment")
async def get_top_sentiment_drivers(
    limit: int = Query(10, description="Number of top items to return", ge=1, le=100),
    hours: int = Query(24, description="Number of hours to look back", ge=1, le=168),
    sentiment_type: str = Query("positive", description="Sentiment type (positive, negative)")
):
    """
    Get the top sentiment drivers (most positive or negative items).
    
    Args:
        limit: Number of items to return
        hours: Hours to look back
        sentiment_type: 'positive' or 'negative'
        
    Returns:
        List of top sentiment drivers with scores and metadata
    """
    try:
        if sentiment_type not in ("positive", "negative"):
            raise HTTPException(
                status_code=400,
                detail="Sentiment type must be 'positive' or 'negative'"
            )
        
        config = get_settings()
        init_db(config.DB_URL)
        engine = get_engine()
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with Session(engine) as session:
            # Build query based on sentiment type
            stmt = select(ScoredItem).where(ScoredItem.ts >= cutoff_time)
            
            if sentiment_type == "positive":
                stmt = stmt.order_by(desc(ScoredItem.polarity))
            else:
                stmt = stmt.order_by(ScoredItem.polarity)
            
            stmt = stmt.limit(limit)
            
            results = session.execute(stmt).scalars().all()
        
        # Convert to response format
        drivers = []
        for item in results:
            drivers.append({
                "id": cast(str, item.id),
                "polarity": float(cast(float, item.polarity)),
                "source": cast(str, item.source),
                "timestamp": cast(datetime, item.ts).isoformat(),
                "probs": item.probs_json
            })
        
        logger.info(
            f"Retrieved top {sentiment_type} sentiment drivers",
            extra={
                'count': len(drivers),
                'limit': limit,
                'hours': hours,
                'sentiment_type': sentiment_type
            }
        )
        
        return {
            "drivers": drivers,
            "count": len(drivers),
            "sentiment_type": sentiment_type,
            "hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving sentiment drivers", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/volume")
async def get_volume_drivers(
    granularity: str = Query("hourly", description="Time granularity (hourly, daily)"),
    days: int = Query(7, description="Number of days to look back", ge=1, le=30)
):
    """
    Get volume statistics by time period.
    
    Args:
        granularity: Time granularity ('hourly', 'daily')
        days: Number of days to look back
        
    Returns:
        Volume statistics grouped by time period
    """
    try:
        if granularity not in ("hourly", "daily"):
            raise HTTPException(
                status_code=400,
                detail="Granularity must be 'hourly' or 'daily'"
            )
        
        config = get_settings()
        init_db(config.DB_URL)
        engine = get_engine()
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        with Session(engine) as session:
            if granularity == "hourly":
                # Group by hour
                time_func = func.strftime('%Y-%m-%d %H:00:00', ScoredItem.ts)
            else:
                # Group by day
                time_func = func.date(ScoredItem.ts)
            
            stmt = (
                select(
                    time_func.label('time_bucket'),
                    func.count(ScoredItem.id).label('volume'),
                    func.avg(ScoredItem.polarity).label('avg_sentiment'),
                    ScoredItem.source
                )
                .where(ScoredItem.ts >= cutoff_time)
                .group_by(time_func, ScoredItem.source)
                .order_by(time_func.desc())
            )
            
            results = session.execute(stmt).all()
        
        # Convert to response format
        volumes = []
        for row in results:
            volumes.append({
                "time_bucket": str(row.time_bucket),
                "volume": int(row.volume),
                "avg_sentiment": float(row.avg_sentiment),
                "source": row.source
            })
        
        logger.info(
            f"Retrieved volume drivers",
            extra={
                'count': len(volumes),
                'granularity': granularity,
                'days': days
            }
        )
        
        return {
            "volumes": volumes,
            "count": len(volumes),
            "granularity": granularity,
            "days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving volume drivers", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/daily", response_model=TopDriversResponse)
async def get_daily_top_drivers(
    target_date: str = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    limit_per_sentiment: int = Query(5, description="Number of items per sentiment type", ge=1, le=20)
) -> TopDriversResponse:
    """
    Get top positive and negative sentiment drivers for a specific day.
    
    Args:
        target_date: Target date in YYYY-MM-DD format (defaults to today)
        limit_per_sentiment: Number of top items to return for each sentiment type
        
    Returns:
        TopDriversResponse with positive and negative drivers for the day
    """
    try:
        # Parse target date or use today
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            parsed_date = date.today()
        
        # Calculate time range for the day
        start_time = datetime.combine(parsed_date, datetime.min.time())
        end_time = datetime.combine(parsed_date, datetime.max.time())
        
        config = get_settings()
        init_db(config.DB_URL)
        engine = get_engine()
        
        # Get raw items to have title and URL information
        raw_items_map = {}
        try:
            # Get raw items for the day (we need these for titles and URLs)
            hours_in_day = 24
            cutoff = datetime.utcnow() - timedelta(hours=hours_in_day * 2)  # Look back 2 days to be safe
            raw_items = get_recent_raw_items(hours=48)  # Last 48 hours
            raw_items_map = {item['id']: item for item in raw_items}
        except Exception as e:
            logger.warning(f"Could not fetch raw items: {e}")
        
        with Session(engine) as session:
            # Get top positive drivers
            positive_stmt = (
                select(ScoredItem)
                .where(ScoredItem.ts >= start_time)
                .where(ScoredItem.ts <= end_time)
                .where(ScoredItem.polarity > 0)
                .order_by(desc(ScoredItem.polarity))
                .limit(limit_per_sentiment)
            )
            positive_results = session.execute(positive_stmt).scalars().all()
            
            # Get top negative drivers
            negative_stmt = (
                select(ScoredItem)
                .where(ScoredItem.ts >= start_time)
                .where(ScoredItem.ts <= end_time)
                .where(ScoredItem.polarity < 0)
                .order_by(ScoredItem.polarity)
                .limit(limit_per_sentiment)
            )
            negative_results = session.execute(negative_stmt).scalars().all()
        
        # Convert to TopDriverItem models
        def create_driver_item(scored_item) -> TopDriverItem:
            item_id = cast(str, scored_item.id)
            raw_item = raw_items_map.get(item_id, {})
            
            return TopDriverItem(
                title=raw_item.get('title', 'Unknown Title'),
                polarity=float(cast(float, scored_item.polarity)),
                url=raw_item.get('url', ''),
                source=cast(str, scored_item.source)
            )
        
        positives = [create_driver_item(item) for item in positive_results]
        negatives = [create_driver_item(item) for item in negative_results]
        
        logger.info(
            f"Retrieved daily top drivers",
            extra={
                'date': str(parsed_date),
                'positives_count': len(positives),
                'negatives_count': len(negatives)
            }
        )
        
        return TopDriversResponse(
            day=parsed_date,
            positives=positives,
            negatives=negatives
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving daily top drivers", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")
