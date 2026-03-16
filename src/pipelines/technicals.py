"""
Technical analysis pipeline for BTC Market Setup page.

Fetches 1h and 4h OHLCV candles from Coinbase REST API (no auth required),
computes EMA, VWAP, RSI, ATR, derives market regime and confluence score,
then exports static JSON to api-output/ for GitHub Pages.

Usage:
    python -m src.pipelines.technicals [output_dir]
"""

import json
import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from src.core import get_logger

logger = get_logger(__name__)

# Coinbase Advanced Trade REST (public, no auth)
COINBASE_REST = "https://api.coinbase.com/api/v3/brokerage/market/products"
PRODUCT_ID = "BTC-USD"

# Granularity strings accepted by Coinbase
GRANULARITY_MAP = {
    "1h": "ONE_HOUR",
    "4h": "FOUR_HOUR",
}

# How many candles to fetch per timeframe
CANDLE_LIMITS = {
    "1h": 336,   # 7 days of 1h
    "4h": 90,    # ~15 days of 4h
}


# ---------------------------------------------------------------------------
# Coinbase OHLCV fetch
# ---------------------------------------------------------------------------

def fetch_candles(granularity: str, limit: int) -> List[Dict[str, Any]]:
    """
    Fetch OHLCV candles from Coinbase Advanced Trade REST API.

    Args:
        granularity: "1h" or "4h"
        limit: Max number of candles (Coinbase max = 350)

    Returns:
        List of dicts with keys: ts, open, high, low, close, volume
        Sorted oldest-first.
    """
    gran_key = GRANULARITY_MAP.get(granularity)
    if not gran_key:
        raise ValueError(f"Unsupported granularity: {granularity}")

    end_ts = int(datetime.now(timezone.utc).timestamp())
    # Coinbase needs integer seconds, go back enough to cover limit candles
    seconds_per_candle = {"1h": 3600, "4h": 14400}[granularity]
    start_ts = end_ts - (limit * seconds_per_candle)

    url = f"{COINBASE_REST}/{PRODUCT_ID}/candles"
    params = {
        "start": str(start_ts),
        "end": str(end_ts),
        "granularity": gran_key,
    }

    logger.info("Fetching candles", extra={"granularity": granularity, "limit": limit})
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            raw = resp.json().get("candles", [])
            # Coinbase returns newest-first; reverse to oldest-first
            candles = []
            for c in reversed(raw):
                candles.append({
                    "ts": int(c["start"]),
                    "open": float(c["open"]),
                    "high": float(c["high"]),
                    "low": float(c["low"]),
                    "close": float(c["close"]),
                    "volume": float(c["volume"]),
                })
            logger.info("Candles fetched", extra={"granularity": granularity, "count": len(candles)})
            return candles
        except Exception as e:
            logger.warning("Candle fetch failed", extra={"attempt": attempt + 1, "error": str(e)})
            if attempt == 2:
                raise
    return []


# ---------------------------------------------------------------------------
# Indicator math (pure Python, no external TA lib needed)
# ---------------------------------------------------------------------------

def ema(values: List[float], period: int) -> List[Optional[float]]:
    """Exponential moving average. Returns list same length as input, None for warmup."""
    result: List[Optional[float]] = [None] * len(values)
    if len(values) < period:
        return result
    k = 2 / (period + 1)
    # Seed with SMA
    seed = sum(values[:period]) / period
    result[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        val = values[i] * k + prev * (1 - k)
        result[i] = val
        prev = val
    return result


def rsi(closes: List[float], period: int = 14) -> List[Optional[float]]:
    """Wilder's RSI."""
    result: List[Optional[float]] = [None] * len(closes)
    if len(closes) <= period:
        return result
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(closes)):
        g = gains[i - 1]
        l = losses[i - 1]
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100 - (100 / (1 + rs))
    return result


def atr(candles: List[Dict], period: int = 14) -> List[Optional[float]]:
    """Average True Range."""
    result: List[Optional[float]] = [None] * len(candles)
    if len(candles) < 2:
        return result
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i - 1]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    if len(trs) < period:
        return result
    avg = sum(trs[:period]) / period
    result[period] = avg
    for i in range(period + 1, len(candles)):
        avg = (avg * (period - 1) + trs[i - 1]) / period
        result[i] = avg
    return result


def vwap_from_candles(candles: List[Dict]) -> List[Optional[float]]:
    """
    Session VWAP (resets at UTC midnight).
    Uses HLC3 as typical price per candle.
    """
    result: List[Optional[float]] = [None] * len(candles)
    cum_pv = 0.0
    cum_v = 0.0
    current_day = None

    for i, c in enumerate(candles):
        day = datetime.utcfromtimestamp(c["ts"]).date()
        if day != current_day:
            # New session — reset
            cum_pv = 0.0
            cum_v = 0.0
            current_day = day
        typ = (c["high"] + c["low"] + c["close"]) / 3
        cum_pv += typ * c["volume"]
        cum_v += c["volume"]
        result[i] = cum_pv / cum_v if cum_v > 0 else c["close"]
    return result


def rolling_avg_volume(candles: List[Dict], period: int = 20) -> List[Optional[float]]:
    """SMA of volume."""
    volumes = [c["volume"] for c in candles]
    result: List[Optional[float]] = [None] * len(volumes)
    for i in range(period - 1, len(volumes)):
        result[i] = sum(volumes[i - period + 1: i + 1]) / period
    return result

def rolling_mean(values: List[float], period: int) -> List[Optional[float]]:
    """SMA of any series."""
    result: List[Optional[float]] = [None] * len(values)
    for i in range(period - 1, len(values)):
        result[i] = sum(values[i - period + 1: i + 1]) / period
    return result

def rolling_high(highs: List[float], period: int) -> List[Optional[float]]:
    """Rolling maximum."""
    result: List[Optional[float]] = [None] * len(highs)
    for i in range(period - 1, len(highs)):
        result[i] = max(highs[i - period + 1: i + 1])
    return result

def rolling_low(lows: List[float], period: int) -> List[Optional[float]]:
    """Rolling minimum."""
    result: List[Optional[float]] = [None] * len(lows)
    for i in range(period - 1, len(lows)):
        result[i] = min(lows[i - period + 1: i + 1])
    return result


def compute_support_resistance(candles: List[Dict], lookback: int = 48) -> Tuple[List, List]:
    """
    Simple S/R detection: cluster local swing highs/lows.
    Returns (support_zones, resistance_zones) relative to latest close.
    """
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    current_price = candles[-1]["close"] if candles else 0

    # Find local swing highs and lows (simple: candle whose high/low > neighbors)
    highs, lows = [], []
    for i in range(1, len(recent) - 1):
        if recent[i]["high"] > recent[i - 1]["high"] and recent[i]["high"] > recent[i + 1]["high"]:
            highs.append(recent[i]["high"])
        if recent[i]["low"] < recent[i - 1]["low"] and recent[i]["low"] < recent[i + 1]["low"]:
            lows.append(recent[i]["low"])

    def cluster(prices: List[float], tolerance_pct: float = 0.005) -> List[Dict]:
        if not prices:
            return []
        prices = sorted(prices)
        clusters: List[List[float]] = []
        for p in prices:
            if clusters and abs(p - clusters[-1][-1]) / clusters[-1][-1] <= tolerance_pct:
                clusters[-1].append(p)
            else:
                clusters.append([p])
        zones = []
        for cl in clusters:
            mid = sum(cl) / len(cl)
            spread = max(cl) - min(cl)
            half = max(spread / 2, mid * 0.002)
            strength = min(0.5 + len(cl) * 0.1, 1.0)
            zones.append({
                "low": round(mid - half, 2),
                "high": round(mid + half, 2),
                "strength": round(strength, 2),
            })
        return zones

    support_zones = [z for z in cluster(lows) if z["high"] < current_price]
    resistance_zones = [z for z in cluster(highs) if z["low"] > current_price]

    # Keep closest 3 of each, sorted by proximity to price
    support_zones = sorted(support_zones, key=lambda z: current_price - z["high"])[:3]
    resistance_zones = sorted(resistance_zones, key=lambda z: z["low"] - current_price)[:3]

    return support_zones, resistance_zones


def fibonacci_levels(session_high: float, session_low: float) -> List[Dict]:
    """Fibonacci retracement levels between session high and low."""
    diff = session_high - session_low
    fibs = [(0.236, "23.6%"), (0.382, "38.2%"), (0.5, "50.0%"), (0.618, "61.8%"), (0.786, "78.6%")]
    return [
        {"label": label, "price": round(session_high - ratio * diff, 2)}
        for ratio, label in fibs
    ]


# ---------------------------------------------------------------------------
# Regime + confluence derivation
# ---------------------------------------------------------------------------

def derive_states(
    candles: List[Dict],
    ema9: List[Optional[float]],
    ema21: List[Optional[float]],
    ema50: List[Optional[float]],
    vwap: List[Optional[float]],
    rsi_vals: List[Optional[float]],
    atr_vals: List[Optional[float]],
    avg_vol: List[Optional[float]],
) -> Dict[str, Any]:
    """Derive market regime, price vs VWAP, EMA alignment, volume regime."""
    last = -1
    close = candles[last]["close"]

    def val(series):
        for i in range(len(series) - 1, -1, -1):
            if series[i] is not None:
                return series[i]
        return None

    e9 = val(ema9)
    e21 = val(ema21)
    e50 = val(ema50)
    vw = val(vwap)
    r = val(rsi_vals)
    a = val(atr_vals)
    av = val(avg_vol)
    vol = candles[last]["volume"]

    # EMA alignment
    if e9 and e21 and e50:
        if e9 > e21 > e50:
            ema_alignment = "bullish"
        elif e9 < e21 < e50:
            ema_alignment = "bearish"
        elif e9 > e21:
            ema_alignment = "mixed_bullish"
        else:
            ema_alignment = "mixed_bearish"
    else:
        ema_alignment = "unknown"

    # Price vs VWAP
    if vw:
        diff_pct = (close - vw) / vw
        if diff_pct > 0.003:
            price_vs_vwap = "above"
        elif diff_pct < -0.003:
            price_vs_vwap = "below"
        else:
            price_vs_vwap = "near"
    else:
        price_vs_vwap = "unknown"

    # Volume regime
    if av and av > 0:
        vol_ratio = vol / av
        if vol_ratio < 0.6:
            volume_regime = "low"
        elif vol_ratio > 1.5:
            volume_regime = "elevated"
        else:
            volume_regime = "normal"
    else:
        volume_regime = "normal"

    # Market regime (rules-based)
    bullish = ema_alignment in ("bullish", "mixed_bullish")
    bearish = ema_alignment in ("bearish", "mixed_bearish")

    if a and e21:
        atr_pct = a / close
        # High volatility chop
        if atr_pct > 0.025:
            market_regime = "volatile_chop"
        elif bullish and price_vs_vwap in ("above", "near"):
            market_regime = "trend_up"
        elif bearish and price_vs_vwap in ("below", "near"):
            market_regime = "trend_down"
        else:
            market_regime = "range"
    else:
        market_regime = "range"

    # Trend bias
    if market_regime == "trend_up":
        trend_bias = "bullish"
    elif market_regime == "trend_down":
        trend_bias = "bearish"
    elif ema_alignment in ("mixed_bullish",):
        trend_bias = "slightly_bullish"
    elif ema_alignment in ("mixed_bearish",):
        trend_bias = "slightly_bearish"
    else:
        trend_bias = "neutral"

    return {
        "ema_alignment": ema_alignment,
        "price_vs_vwap": price_vs_vwap,
        "volume_regime": volume_regime,
        "market_regime": market_regime,
        "trend_bias": trend_bias,
        "indicators": {
            "ema9": round(e9, 2) if e9 else None,
            "ema21": round(e21, 2) if e21 else None,
            "ema50": round(e50, 2) if e50 else None,
            "vwap": round(vw, 2) if vw else None,
            "rsi14": round(r, 2) if r else None,
            "atr14": round(a, 2) if a else None,
        },
    }


def compute_confluence_score(
    states: Dict[str, Any],
    support_zones: List[Dict],
    current_price: float,
    rsi_val: Optional[float],
) -> int:
    """Rules-based confluence score 0–100."""
    score = 0

    if states["price_vs_vwap"] == "above":
        score += 20
    elif states["price_vs_vwap"] == "near":
        score += 10

    indicators = states["indicators"]
    e9 = indicators.get("ema9")
    e21 = indicators.get("ema21")
    e50 = indicators.get("ema50")
    if e9 and e21 and e9 > e21:
        score += 20
    if e21 and e50 and e21 > e50:
        score += 10

    if states["volume_regime"] == "elevated":
        score += 15
    elif states["volume_regime"] == "normal":
        score += 7

    if rsi_val is not None:
        if 30 < rsi_val < 70:
            score += 15
        elif 25 <= rsi_val <= 75:
            score += 7

    # Price near support zone
    if support_zones:
        closest_support = max(z["high"] for z in support_zones)
        proximity = (current_price - closest_support) / current_price
        if proximity < 0.01:
            score += 20
        elif proximity < 0.03:
            score += 10

    return min(score, 100)


def confluence_label(score: int) -> str:
    if score <= 35:
        return "weak"
    elif score <= 60:
        return "mixed"
    elif score <= 80:
        return "favorable"
    else:
        return "strong"


def compute_entry_quality(
    candles: List[Dict],
    states: Dict[str, Any],
    confluence_score: int
) -> Dict[str, Any]:
    """Calculate entry quality metrics matching the frontend logic."""
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    
    eq = {
        "label": "Neutral",
        "range_position_7d": None,
        "range_position_14d": None,
        "price_vs_7d_mean": None,
        "price_vs_14d_mean": None,
        "distance_to_3d_high": None,
        "distance_to_7d_high": None
    }
    
    if not candles:
        return eq
        
    current_price = closes[-1]
    
    # Estimate bars per day
    bars_per_day = 24
    if len(candles) > 1:
        diff_s = candles[1]["ts"] - candles[0]["ts"]
        if diff_s > 0:
            bars_per_day = round(86400 / diff_s)
            
    p3d = bars_per_day * 3
    p7d = bars_per_day * 7
    p14d = bars_per_day * 14
    
    c7d = candles[-p7d:] if len(candles) >= p7d else candles
    c14d = candles[-p14d:] if len(candles) >= p14d else candles
    c3d = candles[-p3d:] if len(candles) >= p3d else candles
    
    if c7d:
        h7 = max(c["high"] for c in c7d)
        l7 = min(c["low"] for c in c7d)
        eq["range_position_7d"] = (current_price - l7) / (h7 - l7) if h7 > l7 else 0.5
        mean7 = sum(c["close"] for c in c7d) / len(c7d)
        eq["price_vs_7d_mean"] = (current_price - mean7) / mean7
        eq["distance_to_7d_high"] = (current_price - h7) / h7
        
    if c14d:
        h14 = max(c["high"] for c in c14d)
        l14 = min(c["low"] for c in c14d)
        eq["range_position_14d"] = (current_price - l14) / (h14 - l14) if h14 > l14 else 0.5
        mean14 = sum(c["close"] for c in c14d) / len(c14d)
        eq["price_vs_14d_mean"] = (current_price - mean14) / mean14
        
    if c3d:
        h3 = max(c["high"] for c in c3d)
        eq["distance_to_3d_high"] = (current_price - h3) / h3
        
    rp7 = eq["range_position_7d"] or 0.5
    rp14 = eq["range_position_14d"] or 0.5
    pm7 = eq["price_vs_7d_mean"] or 0.0
    d3h = eq["distance_to_3d_high"] or 0.0
    d7h = eq["distance_to_7d_high"] or 0.0
    
    ema_bullish = states["ema_alignment"] in ("bullish", "mixed_bullish")
    ema_neutral_or_bull = ema_bullish or states["ema_alignment"] == "unknown"
    above_vwap = states["price_vs_vwap"] == "above"
    
    if (
        ema_neutral_or_bull and
        -0.03 < pm7 < -0.01 and 
        rp14 <= 0.25 and 
        confluence_score >= 40
    ):
        eq["label"] = "Attractive Long"
        states["trend_bias"] = "Bullish Pullback"
    elif (
        ema_bullish and
        above_vwap and
        rp7 >= 0.85 and
        (abs(d3h) <= 0.01 or abs(d7h) <= 0.01)
    ):
        eq["label"] = "Chase Risk"
    elif rp7 > 0.75:
        eq["label"] = "Weak Long" if ema_bullish else "Avoid"
    elif rp7 < 0.25:
        eq["label"] = "Attractive Long" if ema_bullish else "Neutral"
    
    return dict(eq)


def generate_setup_callout(
    states: Dict[str, Any],
    support_zones: List[Dict],
    resistance_zones: List[Dict],
    confluence_score: int,
    current_price: float,
) -> Dict[str, Any]:
    """Generate the plain-English setup callout box."""
    regime = states["market_regime"]
    bias = states["trend_bias"]

    # Bias label
    bias_labels = {
        "bullish": "Bullish",
        "slightly_bullish": "Cautiously Bullish",
        "neutral": "Neutral",
        "slightly_bearish": "Cautiously Bearish",
        "bearish": "Bearish",
    }
    bias_label = bias_labels.get(bias, "Neutral")

    # Long zone from nearest support
    long_zone = None
    if support_zones:
        s = support_zones[0]
        long_zone = f"${s['low']:,.0f}–${s['high']:,.0f}"

    # TP zone from nearest resistance
    tp_zone = None
    if resistance_zones:
        r = resistance_zones[0]
        tp_zone = f"${r['low']:,.0f}–${r['high']:,.0f}"

    # Invalidation: below second support or -2% from current
    if len(support_zones) >= 2:
        inv = support_zones[1]["low"]
        invalidation = f"Below ${inv:,.0f}"
    elif support_zones:
        inv = support_zones[0]["low"] * 0.99
        invalidation = f"Below ${inv:,.0f}"
    else:
        inv = current_price * 0.98
        invalidation = f"Below ${inv:,.0f}"

    # Plain-English summary
    vwap_phrase = {
        "above": "above VWAP",
        "below": "below VWAP",
        "near": "near VWAP",
    }.get(states["price_vs_vwap"], "")

    ema_phrase = {
        "bullish": "EMA alignment is bullish",
        "mixed_bullish": "short-term EMAs turning bullish",
        "mixed_bearish": "short-term EMAs weakening",
        "bearish": "EMA alignment is bearish",
    }.get(states["ema_alignment"], "EMA alignment is mixed")

    vol_phrase = {
        "elevated": "volume confirming the move",
        "normal": "volume is average",
        "low": "volume is light — treat with caution",
    }.get(states["volume_regime"], "")

    summary = f"BTC is {vwap_phrase}. {ema_phrase}. {vol_phrase}.".strip()

    return {
        "bias": bias_label,
        "long_zone": long_zone,
        "invalidation": invalidation,
        "take_profit_zone": tp_zone,
        "summary": summary,
        "confluence_label": confluence_label(confluence_score),
    }


# ---------------------------------------------------------------------------
# Main pipeline functions
# ---------------------------------------------------------------------------

def process_timeframe(granularity: str) -> Dict[str, Any]:
    """Fetch, compute, and return full indicator set for a single timeframe."""
    limit = CANDLE_LIMITS[granularity]
    candles = fetch_candles(granularity, limit)

    if not candles:
        return {"error": f"No candles returned for {granularity}"}

    closes = [c["close"] for c in candles]

    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    e50 = ema(closes, 50)
    vwaps = vwap_from_candles(candles)
    rsi_vals = rsi(closes, 14)
    atr_vals = atr(candles, 14)
    avg_vols = rolling_avg_volume(candles, 20)

    def safe(v):
        return round(v, 4) if v is not None else None

    enriched = []
    for i, c in enumerate(candles):
        enriched.append({
            "ts": datetime.utcfromtimestamp(c["ts"]).isoformat() + "Z",
            "open": c["open"],
            "high": c["high"],
            "low": c["low"],
            "close": c["close"],
            "volume": c["volume"],
            "ema9": safe(e9[i]),
            "ema21": safe(e21[i]),
            "ema50": safe(e50[i]),
            "vwap": safe(vwaps[i]),
            "rsi14": safe(rsi_vals[i]),
            "atr14": safe(atr_vals[i]),
            "avg_volume": safe(avg_vols[i]),
        })

    return {
        "granularity": granularity,
        "updated": datetime.utcnow().isoformat() + "Z",
        "candles": enriched,
    }


def run_technicals(output_dir: str = "api-output") -> None:
    """Run the full technicals pipeline and export JSON files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    tech_path = output_path / "technicals"
    tech_path.mkdir(exist_ok=True)
    signals_path = output_path / "signals"
    signals_path.mkdir(exist_ok=True)

    logger.info("Starting technicals pipeline")

    # ---- 1h timeframe ----
    logger.info("Processing 1h candles")
    data_1h = process_timeframe("1h")
    with open(tech_path / "hourly.json", "w") as f:
        json.dump(data_1h, f, indent=2)

    # ---- 4h timeframe ----
    logger.info("Processing 4h candles")
    data_4h = process_timeframe("4h")
    with open(tech_path / "4h.json", "w") as f:
        json.dump(data_4h, f, indent=2)

    # ---- Derive market state from 1h (primary) ----
    if "error" not in data_1h and data_1h["candles"]:
        candles_1h = []
        for c in data_1h["candles"]:
            candles_1h.append({
                "ts": int(datetime.fromisoformat(c["ts"].replace("Z", "+00:00")).timestamp()),
                "open": c["open"], "high": c["high"], "low": c["low"],
                "close": c["close"], "volume": c["volume"],
            })

        closes = [c["close"] for c in candles_1h]
        e9_v = ema(closes, 9)
        e21_v = ema(closes, 21)
        e50_v = ema(closes, 50)
        vwaps = vwap_from_candles(candles_1h)
        rsi_v = rsi(closes, 14)
        atr_v = atr(candles_1h, 14)
        avg_v = rolling_avg_volume(candles_1h, 20)

        states = derive_states(candles_1h, e9_v, e21_v, e50_v, vwaps, rsi_v, atr_v, avg_v)

        support_zones, resistance_zones = compute_support_resistance(candles_1h)

        current_price = candles_1h[-1]["close"]

        # Session high/low (last 24h = 24 candles for 1h)
        session_candles = candles_1h[-24:]
        session_high = max(c["high"] for c in session_candles)
        session_low = min(c["low"] for c in session_candles)

        # RSI
        rsi_current = None
        for v in reversed(rsi_v):
            if v is not None:
                rsi_current = v
                break

        score = compute_confluence_score(
            states, support_zones, current_price, rsi_current
        )

        setup = generate_setup_callout(
            states, support_zones, resistance_zones, score, current_price
        )

        entry_quality = compute_entry_quality(
            candles_1h, states, score
        )

        market_state = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "price": current_price,
            "market_regime": states["market_regime"],
            "trend_bias": states["trend_bias"],
            "ema_alignment": states["ema_alignment"],
            "price_vs_vwap": states["price_vs_vwap"],
            "volume_regime": states["volume_regime"],
            "confluence_score": score,
            "confluence_label": confluence_label(score),
            "indicators": states["indicators"],
            "setup": setup,
            "entry_quality": entry_quality
        }

        with open(output_path / "market_state.json", "w") as f:
            json.dump(market_state, f, indent=2)

        levels = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "current_price": current_price,
            "session_high": session_high,
            "session_low": session_low,
            "support_zones": support_zones,
            "resistance_zones": resistance_zones,
            "fibonacci_levels": fibonacci_levels(session_high, session_low),
        }

        with open(output_path / "levels.json", "w") as f:
            json.dump(levels, f, indent=2)

        # Signals summary
        signals = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "current": {
                "price": current_price,
                "regime": states["market_regime"],
                "bias": states["trend_bias"],
                "confluence_score": score,
                "confluence_label": confluence_label(score),
                "ema_alignment": states["ema_alignment"],
                "price_vs_vwap": states["price_vs_vwap"],
                "rsi14": round(rsi_current, 2) if rsi_current else None,
            }
        }
        with open(signals_path / "current.json", "w") as f:
            json.dump(signals, f, indent=2)

        logger.info(
            "Market state exported",
            extra={
                "regime": market_state["market_regime"],
                "confluence": score,
                "price": current_price,
            },
        )
    else:
        logger.error("Could not derive market state — no 1h candle data")

    logger.info("Technicals pipeline complete")


