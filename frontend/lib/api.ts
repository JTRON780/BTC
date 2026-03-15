/**
 * API client for BTC Sentiment Analysis backend
 * 
 * Now uses GitHub Pages static JSON API instead of Render backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://jtron780.github.io/BTC';

export interface SentimentDataPoint {
  ts: string;
  raw: number;
  smoothed: number;
  n_posts: number;
  n_positive: number;
  n_negative: number;
  directional_bias: number;
}

export interface SentimentResponse {
  granularity: string;
  data: SentimentDataPoint[];
}

export interface PriceData {
  price: number;
  price_change_24h: number;
  volume_24h: number;
  last_updated: string;
}

export interface TopDriver {
  title: string;
  polarity: number;
  url: string;
  source: string;
}

export interface TopDriversResponse {
  day: string;
  positives: TopDriver[];
  negatives: TopDriver[];
}

/**
 * Fetch sentiment index data
 */
export async function fetchSentimentIndex(
  granularity: 'hourly' | 'daily' = 'daily'
): Promise<SentimentResponse> {
  const res = await fetch(
    `${API_BASE_URL}/sentiment_${granularity}.json`,
    { cache: 'no-store' }
  );

  if (!res.ok) {
    throw new Error(`Failed to fetch sentiment data: ${res.statusText}`);
  }

  return res.json();
}

/**
 * Fetch top sentiment drivers for a specific day
 */
export async function fetchTopDrivers(day: string): Promise<TopDriversResponse> {
  const res = await fetch(
    `${API_BASE_URL}/drivers/${day}.json`,
    { cache: 'no-store' }
  );

  if (!res.ok) {
    if (res.status === 404) {
      return { day, positives: [], negatives: [] };
    }
    throw new Error(`Failed to fetch top drivers: ${res.statusText}`);
  }

  return res.json();
}

/**
 * Fetch current Bitcoin price with 24h change
 */
export async function fetchCurrentPrice(): Promise<PriceData> {
  const response = await fetch(`${API_BASE_URL}/price.json`, {
    cache: 'no-store', // Always get fresh price data
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch price: ${response.statusText}`);
  }

  const data: PriceData = await response.json();
  return data;
}

/**
 * Health check (index.json for GitHub Pages)
 */
export async function checkHealth(): Promise<{ status: string; time: string }> {
  const res = await fetch(`${API_BASE_URL}/index.json`, { cache: 'no-store' });

  if (!res.ok) {
    throw new Error('API health check failed');
  }

  const data = await res.json();
  return { status: 'ok', time: data.updated };
}

/**
 * Fetch derived market state (regime, confluence score, indicators, setup callout)
 */
export async function fetchMarketState() {
  const res = await fetch(`${API_BASE_URL}/market_state.json`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch market state: ${res.statusText}`);
  return res.json();
}

/**
 * Fetch OHLCV candles with pre-computed indicators for a given timeframe.
 * granularity: 'hourly' | '4h'
 */
export async function fetchTechnicals(granularity: 'hourly' | '4h') {
  const file = granularity === 'hourly' ? 'hourly.json' : '4h.json';
  const res = await fetch(`${API_BASE_URL}/technicals/${file}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch technicals (${granularity}): ${res.statusText}`);
  return res.json();
}

/**
 * Fetch support/resistance levels and Fibonacci retracements.
 */
export async function fetchLevels() {
  const res = await fetch(`${API_BASE_URL}/levels.json`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch levels: ${res.statusText}`);
  return res.json();
}


import { Candle, MarketState, TechnicalsResponse, Levels } from '@/lib/indicators';
import * as MathLib from '@/lib/technicals-math';

/**
 * Fetch live candles directly from Coinbase REST API
 */
export async function fetchLiveCandles(granularity: '1h' | '4h', limit: number): Promise<Candle[]> {
    const granKey = granularity === '1h' ? 'ONE_HOUR' : 'FOUR_HOUR';
    const secondsPerCandle = granularity === '1h' ? 3600 : 14400;
    
    // Coinbase needs integer seconds
    const endTs = Math.floor(Date.now() / 1000);
    const startTs = endTs - (limit * secondsPerCandle);
    
    // Call our own Next.js API route to proxy the browser CORS issue
    const url = `/api/coinbase-candles?start=${startTs}&end=${endTs}&granularity=${granKey}`;
    
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) {
        throw new Error(`Failed to fetch Coinbase candles: ${res.statusText}`);
    }
    
    const data = await res.json();
    const raw = data.candles || [];
    
    // Coinbase returns newest-first; reverse to oldest-first
    const candles: Candle[] = [];
    for (let i = raw.length - 1; i >= 0; i--) {
        const c = raw[i];
        // Standardize timestamps to ISO string matching Python pipeline output
        const tsDate = new Date(parseInt(c.start) * 1000);
        candles.push({
            ts: tsDate.toISOString(),
            open: parseFloat(c.open),
            high: parseFloat(c.high),
            low: parseFloat(c.low),
            close: parseFloat(c.close),
            volume: parseFloat(c.volume)
        });
    }
    
    return candles;
}



/**
 * Compute the live market state directly on the client
 */
export async function computeLiveMarketState(timeframe: '1h' | '4h' = '1h'): Promise<{
    marketState: MarketState;
    technicals: TechnicalsResponse;
    levels: Levels;
}> {
    // 1. Fetch live candles
    const limit = timeframe === '1h' ? 168 : 90; // 7 days of 1h, ~15 days of 4h
    const [candles] = await Promise.all([
        fetchLiveCandles(timeframe, limit)
    ]);

    if (candles.length === 0) {
        throw new Error("No live candles available");
    }

    // 2. Compute indicators
    const closes = candles.map(c => c.close);
    const e9 = MathLib.ema(closes, 9);
    const e21 = MathLib.ema(closes, 21);
    const e50 = MathLib.ema(closes, 50);
    const vwaps = MathLib.vwapFromCandles(candles);
    const rsiVals = MathLib.rsi(closes, 14);
    const atrVals = MathLib.atr(candles, 14);
    const avgVols = MathLib.rollingAvgVolume(candles, 20);

    // 3. Enrich candles for chart (matching Python TechnicalsResponse)
    const enrichedCandles: Candle[] = candles.map((c, i) => ({
        ...c,
        ema9: e9[i] ? Number(e9[i]!.toFixed(4)) : null,
        ema21: e21[i] ? Number(e21[i]!.toFixed(4)) : null,
        ema50: e50[i] ? Number(e50[i]!.toFixed(4)) : null,
        vwap: vwaps[i] ? Number(vwaps[i]!.toFixed(4)) : null,
        rsi14: rsiVals[i] ? Number(rsiVals[i]!.toFixed(4)) : null,
        atr14: atrVals[i] ? Number(atrVals[i]!.toFixed(4)) : null,
        avg_volume: avgVols[i] ? Number(avgVols[i]!.toFixed(4)) : null,
    }));

    const technicals: TechnicalsResponse = {
        granularity: timeframe,
        updated: new Date().toISOString(),
        candles: enrichedCandles
    };

    // 4. Derive Market State & Confluence
    const currentPrice = candles[candles.length - 1].close;
    const states = MathLib.deriveStates(candles, e9, e21, e50, vwaps, rsiVals, atrVals, avgVols);
    const { supportZones, resistanceZones } = MathLib.computeSupportResistance(candles);
    
    // Session high/low (last 24h = 24 candles for 1h, 6 for 4h)
    const sessionLen = timeframe === '1h' ? 24 : 6;
    const sessionCandles = candles.slice(-sessionLen);
    const sessionHigh = Math.max(...sessionCandles.map(c => c.high));
    const sessionLow = Math.min(...sessionCandles.map(c => c.low));

    const fibs = MathLib.fibonacciLevels(sessionHigh, sessionLow);
    
    // RSI Current
    let rsiCurrent: number | null = null;
    for (let i = rsiVals.length - 1; i >= 0; i--) {
        if (rsiVals[i] !== null) {
            rsiCurrent = rsiVals[i];
            break;
        }
    }

    const score = MathLib.computeConfluenceScore(states, supportZones, currentPrice, rsiCurrent);
    const setup = MathLib.generateSetupCallout(states, supportZones, resistanceZones, score, currentPrice);

    const marketState: MarketState = {
        ts: new Date().toISOString(),
        price: currentPrice,
        market_regime: states.market_regime,
        trend_bias: states.trend_bias,
        ema_alignment: states.ema_alignment,
        price_vs_vwap: states.price_vs_vwap,
        volume_regime: states.volume_regime,
        confluence_score: score,
        confluence_label: MathLib.confluenceLabel(score),
        indicators: states.indicators,
        setup: setup
    };

    const levels: Levels = {
        ts: new Date().toISOString(),
        current_price: currentPrice,
        session_high: sessionHigh,
        session_low: sessionLow,
        support_zones: supportZones,
        resistance_zones: resistanceZones,
        fibonacci_levels: fibs.map(f => ({
            label: f.label,
            price: f.price
        }))
    };

    return { marketState, technicals, levels };
}

/**
 * Helper exported for the frontend to re-evaluate the current close vs live price
 */
export function reevaluateWithLiveTick(
    technicals: TechnicalsResponse,
    livePrice: number
): { marketState: MarketState, levels: Levels } {
    // Clone candles to avoid mutating react state
    const candles = [...technicals.candles.map(c => ({...c}))];
    if (candles.length === 0) throw new Error("No candles");
    
    // Override the latest candle's close price
    candles[candles.length - 1].close = livePrice;
    if (livePrice > candles[candles.length - 1].high) candles[candles.length - 1].high = livePrice;
    if (livePrice < candles[candles.length - 1].low) candles[candles.length - 1].low = livePrice;

    const closes = candles.map(c => c.close);
    const e9 = MathLib.ema(closes, 9);
    const e21 = MathLib.ema(closes, 21);
    const e50 = MathLib.ema(closes, 50);
    const vwaps = MathLib.vwapFromCandles(candles);
    const rsiVals = MathLib.rsi(closes, 14);
    const atrVals = MathLib.atr(candles, 14);
    const avgVols = MathLib.rollingAvgVolume(candles, 20);

    const states = MathLib.deriveStates(candles, e9, e21, e50, vwaps, rsiVals, atrVals, avgVols);
    const { supportZones, resistanceZones } = MathLib.computeSupportResistance(candles);

    const timeframe = technicals.granularity;
    const sessionLen = timeframe === '1h' ? 24 : 6;
    const sessionCandles = candles.slice(-sessionLen);
    const sessionHigh = Math.max(...sessionCandles.map(c => c.high));
    const sessionLow = Math.min(...sessionCandles.map(c => c.low));
    const fibs = MathLib.fibonacciLevels(sessionHigh, sessionLow);

    let rsiCurrent: number | null = null;
    for (let i = rsiVals.length - 1; i >= 0; i--) {if (rsiVals[i] !== null) { rsiCurrent = rsiVals[i]; break; }}

    const score = MathLib.computeConfluenceScore(states, supportZones, livePrice, rsiCurrent);
    const setup = MathLib.generateSetupCallout(states, supportZones, resistanceZones, score, livePrice);

    const marketState: MarketState = {
        ts: new Date().toISOString(),
        price: livePrice,
        market_regime: states.market_regime,
        trend_bias: states.trend_bias,
        ema_alignment: states.ema_alignment,
        price_vs_vwap: states.price_vs_vwap,
        volume_regime: states.volume_regime,
        confluence_score: score,
        confluence_label: MathLib.confluenceLabel(score),
        indicators: states.indicators,
        setup: setup
    };

    const levels: Levels = {
        ts: new Date().toISOString(),
        current_price: livePrice,
        session_high: sessionHigh,
        session_low: sessionLow,
        support_zones: supportZones,
        resistance_zones: resistanceZones,
        fibonacci_levels: fibs.map(f => ({ label: f.label, price: f.price }))
    };

    return { marketState, levels };
}
