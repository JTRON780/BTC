"""
NLP sentiment analysis pipeline for the BTC sentiment analysis application.

This module provides text preprocessing and sentiment scoring functionality.
"""

from src.nlp.preprocess import clean_text, compose_text
from src.nlp.models import SentimentModel

__all__ = [
    'clean_text',
    'compose_text',
    'SentimentModel',
]
