/**
 * Client-side technical indicator utilities for Market Setup page.
 * All calculations are pure TypeScript — no external TA library needed.
 */

export interface Candle {
    ts: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ema9?: number | null;
    ema21?: number | null;
    ema50?: number | null;
    vwap?: number | null;
    rsi14?: number | null;
    atr14?: number | null;
    avg_volume?: number | null;
}

export interface MarketState {
    ts: string;
    price: number;
    market_regime: string;
    trend_bias: string;
    ema_alignment: string;
    price_vs_vwap: string;
    volume_regime: string;
    confluence_score: number;
    confluence_label: string;
    indicators: {
        ema9: number | null;
        ema21: number | null;
        ema50: number | null;
        vwap: number | null;
        rsi14: number | null;
        atr14: number | null;
    };
    setup: SetupCallout;
}

export interface SetupCallout {
    bias: string;
    long_zone: string | null;
    invalidation: string;
    take_profit_zone: string | null;
    summary: string;
    confluence_label: string;
}

export interface Divergence {
    type: string;
    price_change_24h_pct: number;
    sentiment_change_24h: number | null;
    volume_confirming: boolean;
    headline: string;
    detail: string;
    signal: 'bullish' | 'bearish' | 'neutral';
}

export interface PriceLevel {
    low: number;
    high: number;
    strength: number;
}

export interface FibLevel {
    label: string;
    price: number;
}

export interface Levels {
    ts: string;
    current_price: number;
    session_high: number;
    session_low: number;
    support_zones: PriceLevel[];
    resistance_zones: PriceLevel[];
    fibonacci_levels: FibLevel[];
}

export interface TechnicalsResponse {
    granularity: string;
    updated: string;
    candles: Candle[];
}

/**
 * Aggregate 1h candles into 4h or larger timeframes client-side.
 */
export function aggregateCandles(candles: Candle[], minutesPerBar: number): Candle[] {
    if (!candles.length) return [];
    const hoursPerBar = minutesPerBar / 60;
    const groups: Candle[][] = [];
    let current: Candle[] = [];

    for (const c of candles) {
        const h = new Date(c.ts).getUTCHours();
        const barIndex = Math.floor(h / hoursPerBar);
        if (
            current.length > 0 &&
            Math.floor(new Date(current[0].ts).getUTCHours() / hoursPerBar) !== barIndex
        ) {
            groups.push(current);
            current = [];
        }
        current.push(c);
    }
    if (current.length) groups.push(current);

    return groups.map((g) => ({
        ts: g[0].ts,
        open: g[0].open,
        high: Math.max(...g.map((c) => c.high)),
        low: Math.min(...g.map((c) => c.low)),
        close: g[g.length - 1].close,
        volume: g.reduce((s, c) => s + c.volume, 0),
    }));
}

/**
 * Regime → human-readable badge config.
 */
export function regimeConfig(regime: string): { label: string; color: string; bg: string } {
    const map: Record<string, { label: string; color: string; bg: string }> = {
        trend_up: { label: 'Bullish Trend ↑', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' },
        trend_down: { label: 'Bearish Trend ↓', color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30' },
        range: { label: 'Range Bound ↔', color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/30' },
        volatile_chop: { label: 'Volatile Chop ⚡', color: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/30' },
    };
    return map[regime] ?? { label: regime, color: 'text-slate-400', bg: 'bg-slate-400/10 border-slate-400/30' };
}

/**
 * Confluence score → color class.
 */
export function confluenceColor(score: number): string {
    if (score >= 75) return 'text-emerald-400';
    if (score >= 55) return 'text-yellow-400';
    if (score >= 35) return 'text-orange-400';
    return 'text-red-400';
}

/**
 * Format price as USD string.
 */
export function fmtPrice(price: number | null | undefined): string {
    if (price == null) return '—';
    return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

/**
 * Format percent.
 */
export function fmtPct(value: number | null | undefined, decimals = 2): string {
    if (value == null) return '—';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(decimals)}%`;
}
