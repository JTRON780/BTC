"""
Text preprocessing utilities for NLP sentiment analysis.

This module provides text cleaning and composition functions to prepare
raw text data for sentiment analysis models.
"""

import re
from typing import Optional


def clean_text(text: Optional[str]) -> str:
    """
    Clean and normalize text for sentiment analysis.
    
    Performs the following operations:
    1. Converts text to lowercase
    2. Removes URLs (http/https links)
    3. Collapses multiple whitespace into single spaces
    4. Strips leading/trailing whitespace
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned and normalized text string
        
    Example:
        >>> text = "Check out https://example.com   Bitcoin is    GREAT!"
        >>> clean_text(text)
        'check out bitcoin is great!'
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs (http/https)
    text = re.sub(r'http\S+', '', text)
    
    # Collapse multiple whitespace into single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def compose_text(title: Optional[str], text: Optional[str]) -> str:
    """
    Safely concatenate title and body text for analysis.
    
    Combines title and text content with proper spacing. Handles None
    or empty values gracefully. Useful for creating a single text input
    from structured data (e.g., title + article body).
    
    Args:
        title: Title or headline text
        text: Main body text content
        
    Returns:
        Concatenated text with title and body separated by space
        
    Example:
        >>> compose_text("Bitcoin Surges", "Price hits new high today")
        'Bitcoin Surges Price hits new high today'
        >>> compose_text("", "Just the body text")
        'Just the body text'
        >>> compose_text(None, "Body only")
        'Body only'
    """
    # Handle None/empty values
    title = title or ""
    text = text or ""
    
    # Strip whitespace from both
    title = title.strip()
    text = text.strip()
    
    # Concatenate with space if both exist
    if title and text:
        return f"{title} {text}"
    elif title:
        return title
    else:
        return text


# Self-test block
if __name__ == "__main__":
    print("🧪 Testing Text Preprocessing Functions")
    print("=" * 60)
    
    # Test 1: clean_text with URLs
    print("\n📝 Test 1: clean_text() with URLs")
    print("-" * 60)
    
    test_cases = [
        "Check out https://example.com for more info!",
        "BITCOIN TO THE MOON 🚀 http://bit.ly/xyz",
        "Multiple   spaces    here",
        "MiXeD   CaSe   TEXT   https://test.com/path",
        "",
        "   Leading and trailing spaces   "
    ]
    
    for i, test in enumerate(test_cases, 1):
        result = clean_text(test)
        print(f"{i}. Input:  '{test}'")
        print(f"   Output: '{result}'")
        print()
    
    # Test 2: clean_text validation
    print("\n✅ Test 2: clean_text() validation")
    print("-" * 60)
    
    # Should be lowercase
    assert clean_text("HELLO WORLD") == "hello world"
    print("✅ Converts to lowercase")
    
    # Should remove URLs
    assert "http" not in clean_text("Visit http://example.com now")
    assert "https" not in clean_text("Check https://test.com/path")
    print("✅ Removes URLs")
    
    # Should collapse whitespace
    assert clean_text("a    b     c") == "a b c"
    print("✅ Collapses whitespace")
    
    # Should strip edges
    assert clean_text("  hello  ") == "hello"
    print("✅ Strips leading/trailing whitespace")
    
    # Should handle empty
    assert clean_text("") == ""
    assert clean_text(None) == ""
    print("✅ Handles empty/None input")
    
    # Test 3: compose_text
    print("\n📝 Test 3: compose_text()")
    print("-" * 60)
    
    compose_cases = [
        ("Bitcoin Surges", "Price hits new high today"),
        ("", "Just body text"),
        ("Just title", ""),
        (None, "Body only"),
        ("Title only", None),
        ("", ""),
        (None, None),
        ("  Spaces  ", "  everywhere  ")
    ]
    
    for i, (title, body) in enumerate(compose_cases, 1):
        result = compose_text(title, body)
        print(f"{i}. Title: '{title}' | Body: '{body}'")
        print(f"   Result: '{result}'")
        print()
    
    # Test 4: compose_text validation
    print("\n✅ Test 4: compose_text() validation")
    print("-" * 60)
    
    # Should concatenate both
    assert compose_text("A", "B") == "A B"
    print("✅ Concatenates title and body")
    
    # Should handle empty title
    assert compose_text("", "Body") == "Body"
    assert compose_text(None, "Body") == "Body"
    print("✅ Handles empty/None title")
    
    # Should handle empty body
    assert compose_text("Title", "") == "Title"
    assert compose_text("Title", None) == "Title"
    print("✅ Handles empty/None body")
    
    # Should handle both empty
    assert compose_text("", "") == ""
    assert compose_text(None, None) == ""
    print("✅ Handles both empty/None")
    
    # Should strip whitespace
    assert compose_text("  Title  ", "  Body  ") == "Title Body"
    print("✅ Strips whitespace from both parts")
    
    # Test 5: Integration example
    print("\n📋 Test 5: Integration example")
    print("-" * 60)
    
    raw_title = "BREAKING: Bitcoin Hits $100K! https://news.com/btc"
    raw_body = "The price   of Bitcoin reached   an all-time high today. Visit https://example.com for details."
    
    # Compose then clean (typical workflow)
    composed = compose_text(raw_title, raw_body)
    cleaned = clean_text(composed)
    
    print(f"Original title: '{raw_title}'")
    print(f"Original body:  '{raw_body}'")
    print(f"\nComposed: '{composed}'")
    print(f"\nCleaned:  '{cleaned}'")
    
    # Verify URLs are removed and text is normalized
    assert "http" not in cleaned
    assert "https" not in cleaned
    assert cleaned == cleaned.lower()
    print("\n✅ Integration example passed")
    
    print("\n" + "=" * 60)
    print("✅ All preprocessing tests passed!")
