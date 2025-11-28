"""
Entry point for running the BTC Sentiment Analysis app as a module.

Usage:
    python -m src.app          # Launch dashboard
    python -m src.app api      # Launch API server
"""

from src.app import main

if __name__ == "__main__":
    main()
