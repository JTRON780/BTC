# TODO and Missing Features Analysis

## Executive Summary

This document provides a comprehensive analysis of all TODOs, incomplete implementations, and missing features in the BTC Sentiment Analysis project.

---

## 🔴 Critical Issues

### 1. **`src/nlp/sentiment.py` - Empty File (TODO)**

**Location:** `src/nlp/sentiment.py`  
**Status:** File contains only `# TODO` comment  
**Impact:** **LOW** - Functionality is implemented elsewhere

**Analysis:**
- The file is completely empty except for a TODO comment
- However, sentiment analysis functionality is **fully implemented** in:
  - `src/nlp/models.py` - Contains `SentimentModel` class
  - `src/pipelines/score.py` - Contains scoring pipeline logic
- The `src/nlp/__init__.py` correctly exports from `models.py`, not `sentiment.py`

**Why it exists:**
- Likely a placeholder for future sentiment-specific utilities
- May have been intended for sentiment-specific helper functions separate from the model wrapper
- Could be for sentiment post-processing, thresholding, or classification logic

**Recommendation:**
- **Option 1:** Delete the file if not needed
- **Option 2:** Implement sentiment-specific utilities (e.g., sentiment classification thresholds, confidence scoring)
- **Option 3:** Add documentation explaining why it's intentionally empty

---

### 2. **Missing "Unscored Items" Filter Logic**

**Location:** `src/pipelines/score.py::get_unscored_items()`  
**Status:** **CRITICAL BUG** - Function doesn't actually filter unscored items  
**Impact:** **HIGH** - Will re-score items multiple times, wasting compute

**Current Implementation:**
```python
def get_unscored_items(hours: int = 24) -> List[Dict[str, Any]]:
    """Retrieve recent raw items that haven't been scored yet."""
    logger.info(f"Fetching unscored items", extra={'hours': hours})
    # Get recent raw items
    items = get_recent_raw_items(hours=hours)  # ❌ Gets ALL raw items!
    logger.info(f"Found raw items", extra={'count': len(items)})
    return items
```

**Problem:**
- Function name suggests it filters out already-scored items
- **Actually returns ALL raw items** from the time window
- Relies on `save_scores()` using `INSERT OR IGNORE` to prevent duplicates
- This means:
  - Items are re-processed through the NLP model unnecessarily
  - Wastes compute resources and time
  - Could cause inconsistent scoring if model behavior changes

**Expected Behavior:**
Should query `raw_items` and exclude items where `id` exists in `scored_items`:
```python
# Pseudo-code for correct implementation
SELECT r.* FROM raw_items r
LEFT JOIN scored_items s ON r.id = s.id
WHERE r.ts >= cutoff_time AND s.id IS NULL
```

**Recommendation:**
- **URGENT:** Implement proper SQL query to filter out already-scored items
- This is a performance and correctness issue

---

## 🟡 Incomplete Features

### 3. **Source Filtering in Sentiment Index API**

**Location:** `src/api/routes/index.py::get_sentiment_indices()`  
**Status:** Parameter exists but not implemented  
**Impact:** **MEDIUM** - Feature advertised but doesn't work

**Current Implementation:**
```python
@router.get("/", response_model=SentimentResponse)
async def get_sentiment_indices(
    source: Optional[str] = Query(None, description="Filter by data source")
) -> SentimentResponse:
    # ...
    if source:
        logger.warning(
            "Source filtering requested but not supported in current schema",
            extra={'source': source}
        )
```

**Problem:**
- API accepts `source` parameter
- Logs a warning but doesn't filter
- `SentimentIndex` schema doesn't have a `source` field
- Aggregation pipeline combines all sources into single indices

**Root Cause:**
- `SentimentIndex` table stores combined sentiment (all sources merged)
- Aggregation in `pipelines/aggregate.py` combines all sources
- No per-source sentiment indices are stored

**Recommendation:**
- **Option 1:** Remove the `source` parameter (simplest)
- **Option 2:** Add `source` field to `SentimentIndex` schema and modify aggregation
- **Option 3:** Filter at query time by joining with `ScoredItem` (less efficient)

---

### 4. **Empty `__init__.py` Files**

**Locations:**
- `src/api/__init__.py` - Contains only `# TODO`
- `src/api/routes/__init__.py` - Contains only `# TODO`
- `src/ingest/__init__.py` - Contains only `# TODO`
- `src/tests/__init__.py` - Contains only `# TODO`

**Status:** **LOW PRIORITY** - Python packages work without explicit exports

**Analysis:**
- These files are placeholders
- Python packages work fine with empty `__init__.py` files
- However, explicit exports improve code clarity and IDE support

**Recommendation:**
- Add proper `__all__` exports for better API clarity
- Or remove TODO comments if intentionally minimal

---

### 5. **Incomplete Test Suite**

**Location:** `src/tests/test_ingest.py`  
**Status:** Contains only placeholder test  
**Impact:** **MEDIUM** - Missing test coverage for ingestion module

**Current Implementation:**
```python
# TODO

def test_placeholder():
    assert True
```

**Missing Tests:**
- No tests for `fetch_news_feeds()`
- No tests for `fetch_reddit_feeds()`
- No tests for `fetch_price_snapshot()`
- No tests for `backfill_prices()`
- No tests for feed parsing and normalization

**Recommendation:**
- Implement comprehensive tests for ingestion module
- Test error handling (network failures, malformed feeds)
- Test duplicate detection
- Mock external API calls

---

## 🟢 Minor Issues / Documentation

### 6. **Dashboard "Volatility" Metric Mentioned but Not Implemented**

**Location:** `README.md` line 49  
**Status:** Documentation mentions feature not in code

**README Claims:**
> "Real-time KPI cards (Current Index, 24h Change, Volatility)"

**Actual Implementation:**
- Current Sentiment ✅
- Raw Sentiment ✅
- 24h Change ✅
- 7d Change ✅
- **Volatility** ❌ Missing

**Recommendation:**
- Either implement volatility calculation (standard deviation of sentiment)
- Or remove from README

---

### 7. **Missing `.env.example` File**

**Location:** Root directory  
**Status:** README references `.env.example` but file doesn't exist

**README Says:**
```bash
cp .env.example .env
```

**Recommendation:**
- Create `.env.example` with all required environment variables
- Document each variable's purpose

---

## 📊 Summary Table

| Issue | Location | Severity | Impact | Status |
|-------|----------|----------|--------|--------|
| Empty `sentiment.py` | `src/nlp/sentiment.py` | Low | None | Placeholder |
| Missing unscored filter | `src/pipelines/score.py` | **Critical** | **High** | **Bug** |
| Source filtering | `src/api/routes/index.py` | Medium | Medium | Incomplete |
| Empty `__init__.py` files | Multiple | Low | Low | Placeholders |
| Incomplete tests | `src/tests/test_ingest.py` | Medium | Medium | Missing |
| Volatility metric | `README.md` | Low | Low | Documentation |
| Missing `.env.example` | Root | Low | Low | Missing file |

---

## 🎯 Recommended Action Plan

### Priority 1 (Critical - Fix Immediately)
1. **Fix `get_unscored_items()`** - Implement proper SQL filtering to exclude already-scored items
   - Prevents unnecessary re-processing
   - Improves performance
   - Ensures correctness

### Priority 2 (Important - Fix Soon)
2. **Complete test suite** - Add tests for ingestion module
3. **Fix source filtering** - Either implement or remove the parameter
4. **Create `.env.example`** - Document required environment variables

### Priority 3 (Nice to Have)
5. **Clean up TODOs** - Either implement or document why files are empty
6. **Add volatility metric** - Implement or remove from README
7. **Improve `__init__.py` files** - Add proper exports

---

## 🔍 Code Quality Notes

**Positive Aspects:**
- Most functionality is well-implemented
- Good error handling in most places
- Comprehensive documentation
- Proper type hints throughout

**Areas for Improvement:**
- The unscored items bug is a significant issue
- Some incomplete features are advertised but not working
- Test coverage could be improved

---

## 📝 Implementation Suggestions

### Fix for `get_unscored_items()`:

```python
def get_unscored_items(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Retrieve recent raw items that haven't been scored yet.
    
    Uses LEFT JOIN to exclude items that already exist in scored_items.
    """
    engine = get_engine()
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    with Session(engine) as session:
        # Query raw items that don't have corresponding scored items
        stmt = (
            select(RawItem)
            .outerjoin(ScoredItem, RawItem.id == ScoredItem.id)
            .where(RawItem.ts >= cutoff_time)
            .where(ScoredItem.id.is_(None))  # Only items NOT in scored_items
            .order_by(RawItem.ts.desc())
        )
        
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                'id': item.id,
                'source': item.source,
                'ts': item.ts,
                'title': item.title,
                'text': item.text,
                'url': item.url,
                'created_at': item.created_at
            }
            for item in results
        ]
```

---

**Generated:** 2025-01-XX  
**Last Updated:** 2025-01-XX

