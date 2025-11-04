"""
Pydantic models for sentiment analysis API responses.

This module defines the data models used in API responses for sentiment
analysis endpoints, including sentiment indices and top drivers.
"""

from datetime import datetime, date
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class SentimentIndexPoint(BaseModel):
    """
    A single sentiment index data point.
    
    Represents sentiment data for a specific time window with both raw
    and smoothed sentiment values along with the number of posts analyzed.
    """
    
    ts: datetime = Field(
        description="Timestamp for this sentiment reading",
        examples=["2025-11-04T12:00:00Z"]
    )
    raw: float = Field(
        description="Raw aggregated sentiment value (-1.0 to 1.0)",
        ge=-1.0,
        le=1.0,
        examples=[0.65, -0.23, 0.12]
    )
    smoothed: float = Field(
        description="EWMA smoothed sentiment value (-1.0 to 1.0)",
        ge=-1.0,
        le=1.0,
        examples=[0.62, -0.19, 0.15]
    )
    n_posts: int = Field(
        description="Number of posts included in this aggregation",
        ge=0,
        examples=[150, 89, 234]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ts": "2025-11-04T12:00:00Z",
                    "raw": 0.65,
                    "smoothed": 0.62,
                    "n_posts": 150
                },
                {
                    "ts": "2025-11-04T13:00:00Z",
                    "raw": -0.23,
                    "smoothed": -0.19,
                    "n_posts": 89
                }
            ]
        }
    )


class SentimentResponse(BaseModel):
    """
    Response model for sentiment index data endpoints.
    
    Contains a list of sentiment data points for a specific time granularity
    (hourly, daily, etc.) with metadata about the response.
    """
    
    granularity: str = Field(
        description="Time granularity of the data points",
        examples=["hourly", "daily", "weekly"]
    )
    data: List[SentimentIndexPoint] = Field(
        description="List of sentiment index data points",
        examples=[[
            {
                "ts": "2025-11-04T12:00:00Z",
                "raw": 0.65,
                "smoothed": 0.62,
                "n_posts": 150
            }
        ]]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "granularity": "hourly",
                    "data": [
                        {
                            "ts": "2025-11-04T12:00:00Z",
                            "raw": 0.65,
                            "smoothed": 0.62,
                            "n_posts": 150
                        },
                        {
                            "ts": "2025-11-04T13:00:00Z",
                            "raw": -0.23,
                            "smoothed": -0.19,
                            "n_posts": 89
                        }
                    ]
                },
                {
                    "granularity": "daily",
                    "data": [
                        {
                            "ts": "2025-11-04T00:00:00Z",
                            "raw": 0.42,
                            "smoothed": 0.38,
                            "n_posts": 1247
                        }
                    ]
                }
            ]
        }
    )


class TopDriverItem(BaseModel):
    """
    A single top driver item (highly positive or negative sentiment).
    
    Represents an individual post/article that significantly influenced
    sentiment in a positive or negative direction.
    """
    
    title: str = Field(
        description="Title or headline of the content",
        examples=[
            "Bitcoin Breaks $100K Barrier!",
            "Crypto Market Crashes 20%",
            "Major Bank Adopts Bitcoin"
        ]
    )
    polarity: float = Field(
        description="Sentiment polarity score (-1.0 to 1.0)",
        ge=-1.0,
        le=1.0,
        examples=[0.89, -0.76, 0.23]
    )
    url: str = Field(
        description="Source URL of the content",
        examples=[
            "https://reddit.com/r/bitcoin/comments/abc123",
            "https://cointelegraph.com/news/btc-hits-100k",
            "https://decrypt.co/bitcoin-adoption-news"
        ]
    )
    source: str = Field(
        description="Source platform or publication",
        examples=["reddit", "news", "cointelegraph", "decrypt"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Bitcoin Breaks $100K Barrier!",
                    "polarity": 0.89,
                    "url": "https://cointelegraph.com/news/btc-hits-100k",
                    "source": "news"
                },
                {
                    "title": "This crash is devastating my portfolio",
                    "polarity": -0.76,
                    "url": "https://reddit.com/r/bitcoin/comments/xyz789",
                    "source": "reddit"
                }
            ]
        }
    )


class TopDriversResponse(BaseModel):
    """
    Response model for top sentiment drivers endpoints.
    
    Contains lists of the most positive and negative sentiment drivers
    for a specific day, helping identify what content influenced sentiment.
    """
    
    day: date = Field(
        description="Date for which these drivers were identified",
        examples=["2025-11-04", "2025-11-03"]
    )
    positives: List[TopDriverItem] = Field(
        description="Top positive sentiment drivers for the day",
        examples=[[
            {
                "title": "Bitcoin Breaks $100K Barrier!",
                "polarity": 0.89,
                "url": "https://cointelegraph.com/news/btc-hits-100k",
                "source": "news"
            }
        ]]
    )
    negatives: List[TopDriverItem] = Field(
        description="Top negative sentiment drivers for the day",
        examples=[[
            {
                "title": "This crash is devastating my portfolio",
                "polarity": -0.76,
                "url": "https://reddit.com/r/bitcoin/comments/xyz789",
                "source": "reddit"
            }
        ]]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "day": "2025-11-04",
                    "positives": [
                        {
                            "title": "Bitcoin Breaks $100K Barrier!",
                            "polarity": 0.89,
                            "url": "https://cointelegraph.com/news/btc-hits-100k",
                            "source": "news"
                        },
                        {
                            "title": "Major institutional adoption announcement",
                            "polarity": 0.84,
                            "url": "https://decrypt.co/institutional-bitcoin",
                            "source": "news"
                        }
                    ],
                    "negatives": [
                        {
                            "title": "This crash is devastating my portfolio",
                            "polarity": -0.76,
                            "url": "https://reddit.com/r/bitcoin/comments/xyz789",
                            "source": "reddit"
                        },
                        {
                            "title": "Government crackdown on crypto trading",
                            "polarity": -0.68,
                            "url": "https://cointelegraph.com/news/gov-crackdown",
                            "source": "news"
                        }
                    ]
                }
            ]
        }
    )
