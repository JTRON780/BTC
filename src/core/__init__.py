"""
Core infrastructure module for the BTC sentiment analysis application.

This module provides essential utilities:
- config: Environment configuration management
- logger: JSON-formatted logging
"""

from src.core.config import Config, get_settings
from src.core.logger import get_logger, LOG_LEVEL

__all__ = [
    "Config",
    "get_settings",
    "get_logger",
    "LOG_LEVEL",
]
