"""
Pipeline orchestration for the BTC sentiment analysis application.

This module provides pipeline scripts for data collection, scoring,
aggregation, and automated scheduling.
"""

from src.pipelines.score import run_scoring_pipeline, score_items, get_unscored_items

__all__ = [
    'run_scoring_pipeline',
    'score_items',
    'get_unscored_items',
]
