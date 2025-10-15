"""
JSON-formatted logging utility for the BTC sentiment analysis application.

This module provides a centralized logging configuration using JSON formatting
for structured log output. Logs include timestamp, level, module, and message fields.
"""

import logging
import os
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger


# Global log level from environment, default to INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Create and return a JSON-formatted logger instance.
    
    This factory function creates a logger with JSON formatting that includes
    timestamp, level, module name, and message fields. Logs are written to stdout.
    
    Args:
        name: Name of the logger (typically __name__ of the calling module)
        level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If not provided, uses the global LOG_LEVEL from environment
    
    Returns:
        logging.Logger: Configured logger instance with JSON formatting
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", extra={"user_id": 123})
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or LOG_LEVEL
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Avoid adding handlers multiple times if logger already exists
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
        rename_fields={
            "levelname": "level",
            "name": "module",
            "asctime": "timestamp"
        },
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger


if __name__ == "__main__":
    # Demonstration of the logger functionality
    print("="*60)
    print("Testing JSON Logger")
    print("="*60)
    
    # Create logger instance
    logger = get_logger(__name__)
    
    # Test different log levels
    logger.debug("This is a DEBUG message (may not appear if LOG_LEVEL=INFO)")
    logger.info("Application started successfully")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Test with extra fields
    logger.info(
        "User action logged",
        extra={
            "user_id": 12345,
            "action": "login",
            "ip_address": "192.168.1.100"
        }
    )
    
    # Test different log levels by creating loggers with specific levels
    print("\n" + "="*60)
    print("Testing DEBUG level logger")
    print("="*60)
    debug_logger = get_logger("debug_test", level="DEBUG")
    debug_logger.debug("This DEBUG message should now appear")
    debug_logger.info("This INFO message should appear")
    
    print("\n" + "="*60)
    print("Testing ERROR level logger")
    print("="*60)
    error_logger = get_logger("error_test", level="ERROR")
    error_logger.info("This INFO message should NOT appear")
    error_logger.error("This ERROR message should appear")
    
    print("\n" + "="*60)
    print(f"Current global LOG_LEVEL: {LOG_LEVEL}")
    print("="*60)
