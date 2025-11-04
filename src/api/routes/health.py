"""
Health check router for the BTC sentiment analysis API.

Provides system health and status endpoints.
"""

from datetime import datetime
from fastapi import APIRouter

from src.core import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Dictionary with status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "btc-sentiment-api"
    }


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for load balancers.
    
    Returns:
        Simple pong response
    """
    return {"message": "pong"}
