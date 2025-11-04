"""
FastAPI application for the BTC sentiment analysis API.

This module creates the FastAPI app with versioned routes, CORS middleware,
and proper error handling.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core import get_logger, get_settings
from src.api.routes import health, index, top_drivers

logger = get_logger(__name__)

# Load configuration
config = get_settings()

# Create FastAPI app
app = FastAPI(
    title="BTC Sentiment Analysis API",
    description="API for Bitcoin sentiment analysis and market intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route
@app.get("/")
async def root():
    """
    Root endpoint returning service status.
    
    Returns:
        Dictionary with service status
    """
    return {"status": "ok"}

# Mount routers under /api/v1/ prefix
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(index.router, prefix="/api/v1/sentiment", tags=["Sentiment"])
app.include_router(top_drivers.router, prefix="/api/v1/drivers", tags=["Drivers"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup handler.
    """
    logger.info("BTC Sentiment Analysis API starting up")
    logger.info(f"Allowed CORS origins: {config.ALLOWED_ORIGINS}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown handler.
    """
    logger.info("BTC Sentiment Analysis API shutting down")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting FastAPI server")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
