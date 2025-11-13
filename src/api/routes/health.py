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
    Health check endpoint for Docker liveness and readiness probes.
    
    Returns simple status indicator with current UTC timestamp.
    This endpoint is designed to be lightweight and always return
    a successful response when the service is running.
    
    Returns:
        Dictionary with status and current UTC time
        
    Example Response:
        {
            "status": "healthy",
            "time": "2025-11-10T15:30:45.123456"
        }
    """
    return {
        "status": "healthy",
        "time": datetime.utcnow().isoformat()
    }


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for load balancers.
    
    Returns:
        Simple pong response
    """
    return {"message": "pong"}
