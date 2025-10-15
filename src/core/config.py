"""
Environment configuration management using Pydantic Settings.

This module provides a centralized configuration class that loads and validates
environment variables for the BTC sentiment analysis application.
"""

from functools import lru_cache
from typing import Any, List, Tuple

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables.
    
    All fields are loaded from environment variables or a .env file.
    Uses Pydantic for validation and type conversion.
    
    Attributes:
        DB_URL: Database connection string (PostgreSQL format)
        NEWS_FEEDS: List of RSS feed URLs for news sources (comma-separated in .env)
        REDDIT_FEEDS: List of Reddit subreddit names to monitor (comma-separated in .env)
        COINGECKO_BASE: Base URL for CoinGecko API
        ALLOWED_ORIGINS: List of allowed CORS origins for the API (comma-separated in .env)
    """
    
    DB_URL: str
    NEWS_FEEDS: str  # Will be parsed to List[str] by model_validator
    REDDIT_FEEDS: str  # Will be parsed to List[str] by model_validator
    COINGECKO_BASE: AnyHttpUrl
    ALLOWED_ORIGINS: str  # Will be parsed to List[str] by model_validator
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @model_validator(mode="after")
    def parse_comma_separated_fields(self) -> "Config":
        """
        Parse comma-separated string fields into lists after model validation.
        
        This validator runs after all field validators and converts string fields
        containing comma-separated values into proper Python lists.
        
        Returns:
            Self with parsed list fields
            
        Raises:
            ValueError: If any URL validation fails
        """
        # Parse NEWS_FEEDS
        if isinstance(self.NEWS_FEEDS, str):
            feeds = [feed.strip() for feed in self.NEWS_FEEDS.split(",") if feed.strip()]
            for url in feeds:
                if not url.startswith(("http://", "https://")):
                    raise ValueError(f"News feed URL must start with http:// or https://: {url}")
            # Type ignore because we're deliberately changing the type post-validation
            self.NEWS_FEEDS = feeds  # type: ignore
        
        # Parse REDDIT_FEEDS
        if isinstance(self.REDDIT_FEEDS, str):
            self.REDDIT_FEEDS = [feed.strip() for feed in self.REDDIT_FEEDS.split(",") if feed.strip()]  # type: ignore
        
        # Parse ALLOWED_ORIGINS
        if isinstance(self.ALLOWED_ORIGINS, str):
            origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
            for url in origins:
                if not url.startswith(("http://", "https://")):
                    raise ValueError(f"Allowed origin must start with http:// or https://: {url}")
            self.ALLOWED_ORIGINS = origins  # type: ignore
        
        return self


@lru_cache()
def get_settings() -> Config:
    """
    Get cached singleton instance of application settings.
    
    This function uses LRU cache to ensure only one Config instance
    is created and reused throughout the application lifecycle.
    
    Returns:
        Config: Cached configuration instance
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.DB_URL)
        >>> print(settings.NEWS_FEEDS)  # Already parsed as list
    """
    return Config()


if __name__ == "__main__":
    # Test configuration loading
    config = Config()
    print("Configuration loaded successfully!")
    print("="*60)
    print("\nIndividual settings:")
    print(f"  DB_URL: {config.DB_URL}")
    print(f"  NEWS_FEEDS: {config.NEWS_FEEDS}")
    print(f"  REDDIT_FEEDS: {config.REDDIT_FEEDS}")
    print(f"  COINGECKO_BASE: {config.COINGECKO_BASE}")
    print(f"  ALLOWED_ORIGINS: {config.ALLOWED_ORIGINS}")
    print("\n" + "="*60)
    print("\nConfiguration dump:")
    print(config.model_dump())
    print("\n" + "="*60)
    print("\nTesting singleton pattern with get_settings():")
    settings1 = get_settings()
    settings2 = get_settings()
    print(f"  Same instance? {settings1 is settings2}")  # Should be True
