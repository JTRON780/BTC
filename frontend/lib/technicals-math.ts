import { Candle } from './indicators';

// ---------------------------------------------------------------------------
// Basic Indicator Math
// ---------------------------------------------------------------------------

export function ema(values: number[], period: number): (number | null)[] {
    const result: (number | null)[] = Array(values.length).fill(null);
    if (values.length < period) return result;

    const k = 2 / (period + 1);
    
    // Seed with SMA
    let sum = 0;
    for (let i = 0; i < period; i++) sum += values[i];
    const seed = sum / period;
    
    result[period - 1] = seed;
    let prev = seed;
    
    for (let i = period; i < values.length; i++) {
        const val = values[i] * k + prev * (1 - k);
        result[i] = val;
        prev = val;
    }
    
    return result;
}

export function rsi(closes: number[], period: number = 14): (number | null)[] {
    const result: (number | null)[] = Array(closes.length).fill(null);
    if (closes.length <= period) return result;

    const gains: number[] = [];
    const losses: number[] = [];
    
    for (let i = 1; i < closes.length; i++) {
        const diff = closes[i] - closes[i - 1];
        gains.push(Math.max(diff, 0));
        losses.push(Math.max(-diff, 0));
    }

    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

    for (let i = period; i < closes.length; i++) {
        const g = gains[i - 1];
        const l = losses[i - 1];
        
        avgGain = (avgGain * (period - 1) + g) / period;
        avgLoss = (avgLoss * (period - 1) + l) / period;
        
        if (avgLoss === 0) {
            result[i] = 100.0;
        } else {
            const rs = avgGain / avgLoss;
            result[i] = 100 - (100 / (1 + rs));
        }
    }
    
    return result;
}

export function atr(candles: Candle[], period: number = 14): (number | null)[] {
    const result: (number | null)[] = Array(candles.length).fill(null);
    if (candles.length < 2) return result;

    const trs: number[] = [];
    for (let i = 1; i < candles.length; i++) {
        const h = candles[i].high;
        const l = candles[i].low;
        const pc = candles[i - 1].close;
        const tr = Math.max(h - l, Math.abs(h - pc), Math.abs(l - pc));
        trs.push(tr);
    }

    if (trs.length < period) return result;

    let avg = trs.slice(0, period).reduce((a, b) => a + b, 0) / period;
    result[period] = avg;

    for (let i = period + 1; i < candles.length; i++) {
        avg = (avg * (period - 1) + trs[i - 1]) / period;
        result[i] = avg;
    }

    return result;
}

export function vwapFromCandles(candles: Candle[]): (number | null)[] {
    const result: (number | null)[] = Array(candles.length).fill(null);
    let cumPv = 0.0;
    let cumV = 0.0;
    let currentDay: number | null = null; // We'll use UTC day of month (1-31)

    for (let i = 0; i < candles.length; i++) {
        const c = candles[i];
        const date = new Date(c.ts);
        const day = date.getUTCDate();
        
        if (day !== currentDay) {
            cumPv = 0.0;
            cumV = 0.0;
            currentDay = day;
        }
        
        const typ = (c.high + c.low + c.close) / 3;
        cumPv += typ * c.volume;
        cumV += c.volume;
        
        result[i] = cumV > 0 ? cumPv / cumV : c.close;
    }
    
    return result;
}

export function rollingAvgVolume(candles: Candle[], period: number = 20): (number | null)[] {
    const volumes = candles.map(c => c.volume);
    const result: (number | null)[] = Array(volumes.length).fill(null);
    
    for (let i = period - 1; i < volumes.length; i++) {
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += volumes[i - j];
        }
        result[i] = sum / period;
    }
    
    return result;
}

// ---------------------------------------------------------------------------
// S/R and Fibonacci
// ---------------------------------------------------------------------------

export interface PriceLevel {
    low: number;
    high: number;
    strength: number;
}

export function computeSupportResistance(candles: Candle[], lookback: number = 48): {
    supportZones: PriceLevel[],
    resistanceZones: PriceLevel[]
} {
    const recent = candles.length >= lookback ? candles.slice(-lookback) : candles;
    const currentPrice = candles.length > 0 ? candles[candles.length - 1].close : 0;

    const highs: number[] = [];
    const lows: number[] = [];

    for (let i = 1; i < recent.length - 1; i++) {
        if (recent[i].high > recent[i - 1].high && recent[i].high > recent[i + 1].high) {
            highs.push(recent[i].high);
        }
        if (recent[i].low < recent[i - 1].low && recent[i].low < recent[i + 1].low) {
            lows.push(recent[i].low);
        }
    }

    function cluster(prices: number[], tolerancePct: number = 0.005): PriceLevel[] {
        if (!prices.length) return [];
        
        prices.sort((a, b) => a - b);
        const clusters: number[][] = [];
        
        for (const p of prices) {
            if (clusters.length > 0) {
                const lastCluster = clusters[clusters.length - 1];
                const lastVal = lastCluster[lastCluster.length - 1];
                if (Math.abs(p - lastVal) / lastVal <= tolerancePct) {
                    lastCluster.push(p);
                } else {
                    clusters.push([p]);
                }
            } else {
                clusters.push([p]);
            }
        }

        const zones: PriceLevel[] = [];
        for (const cl of clusters) {
            const mid = cl.reduce((a, b) => a + b, 0) / cl.length;
            const spread = Math.max(...cl) - Math.min(...cl);
            const half = Math.max(spread / 2, mid * 0.002);
            const strength = Math.min(0.5 + cl.length * 0.1, 1.0);
            
            zones.push({
                low: Number((mid - half).toFixed(2)),
                high: Number((mid + half).toFixed(2)),
                strength: Number(strength.toFixed(2))
            });
        }
        return zones;
    }

    let supportZones = cluster(lows).filter(z => z.high < currentPrice);
    let resistanceZones = cluster(highs).filter(z => z.low > currentPrice);

    supportZones.sort((a, b) => (currentPrice - a.high) - (currentPrice - b.high));
    resistanceZones.sort((a, b) => (a.low - currentPrice) - (b.low - currentPrice));

    return {
        supportZones: supportZones.slice(0, 3),
        resistanceZones: resistanceZones.slice(0, 3)
    };
}

export function fibonacciLevels(sessionHigh: number, sessionLow: number): { label: string, price: number }[] {
    const diff = sessionHigh - sessionLow;
    const fibs = [
        { ratio: 0.236, label: "23.6%" },
        { ratio: 0.382, label: "38.2%" },
        { ratio: 0.5, label: "50.0%" },
        { ratio: 0.618, label: "61.8%" },
        { ratio: 0.786, label: "78.6%" }
    ];
    
    return fibs.map(f => ({
        label: f.label,
        price: Number((sessionHigh - f.ratio * diff).toFixed(2))
    }));
}

// ---------------------------------------------------------------------------
// Regime + confluence derivation
// ---------------------------------------------------------------------------

export function deriveStates(
    candles: Candle[],
    ema9: (number | null)[],
    ema21: (number | null)[],
    ema50: (number | null)[],
    vwap: (number | null)[],
    rsiVals: (number | null)[],
    atrVals: (number | null)[],
    avgVol: (number | null)[]
) {
    const last = candles.length - 1;
    if (last < 0) throw new Error("No candles");
    
    const close = candles[last].close;

    function val(series: (number | null)[]): number | null {
        for (let i = series.length - 1; i >= 0; i--) {
            if (series[i] !== null) return series[i];
        }
        return null;
    }

    const e9 = val(ema9);
    const e21 = val(ema21);
    const e50 = val(ema50);
    const vw = val(vwap);
    const r = val(rsiVals);
    const a = val(atrVals);
    const av = val(avgVol);
    const vol = candles[last].volume;

    let emaAlignment = "unknown";
    if (e9 !== null && e21 !== null && e50 !== null) {
        if (e9 > e21 && e21 > e50) {
            emaAlignment = "bullish";
        } else if (e9 < e21 && e21 < e50) {
            emaAlignment = "bearish";
        } else if (e9 > e21) {
            emaAlignment = "mixed_bullish";
        } else {
            emaAlignment = "mixed_bearish";
        }
    }

    let priceVsVwap = "unknown";
    if (vw !== null) {
        const diffPct = (close - vw) / vw;
        if (diffPct > 0.003) {
            priceVsVwap = "above";
        } else if (diffPct < -0.003) {
            priceVsVwap = "below";
        } else {
            priceVsVwap = "near";
        }
    }

    let volumeRegime = "normal";
    if (av !== null && av > 0) {
        const volRatio = vol / av;
        if (volRatio < 0.6) {
            volumeRegime = "low";
        } else if (volRatio > 1.5) {
            volumeRegime = "elevated";
        } else {
            volumeRegime = "normal";
        }
    }

    const bullish = emaAlignment === "bullish" || emaAlignment === "mixed_bullish";
    const bearish = emaAlignment === "bearish" || emaAlignment === "mixed_bearish";

    let marketRegime = "range";
    if (a !== null && e21 !== null) {
        const atrPct = a / close;
        if (atrPct > 0.025) {
            marketRegime = "volatile_chop";
        } else if (bullish && (priceVsVwap === "above" || priceVsVwap === "near")) {
            marketRegime = "trend_up";
        } else if (bearish && (priceVsVwap === "below" || priceVsVwap === "near")) {
            marketRegime = "trend_down";
        } else {
            marketRegime = "range";
        }
    }

    let trendBias = "neutral";
    if (marketRegime === "trend_up") {
        trendBias = "bullish";
    } else if (marketRegime === "trend_down") {
        trendBias = "bearish";
    } else if (emaAlignment === "mixed_bullish") {
        trendBias = "slightly_bullish";
    } else if (emaAlignment === "mixed_bearish") {
        trendBias = "slightly_bearish";
    }

    return {
        ema_alignment: emaAlignment,
        price_vs_vwap: priceVsVwap,
        volume_regime: volumeRegime,
        market_regime: marketRegime,
        trend_bias: trendBias,
        indicators: {
            ema9: e9 !== null ? Number(e9.toFixed(2)) : null,
            ema21: e21 !== null ? Number(e21.toFixed(2)) : null,
            ema50: e50 !== null ? Number(e50.toFixed(2)) : null,
            vwap: vw !== null ? Number(vw.toFixed(2)) : null,
            rsi14: r !== null ? Number(r.toFixed(2)) : null,
            atr14: a !== null ? Number(a.toFixed(2)) : null,
        }
    };
}

export function computeConfluenceScore(
    states: ReturnType<typeof deriveStates>,
    supportZones: PriceLevel[],
    currentPrice: number,
    rsiVal: number | null
): number {
    let score = 0;

    // VWAP (20 pts max)
    if (states.price_vs_vwap === "above") {
        score += 20;
    } else if (states.price_vs_vwap === "near") {
        score += 10;
    }

    // EMA Cross (20 pts max)
    const { ema9, ema21, ema50 } = states.indicators;
    if (ema9 !== null && ema21 !== null && ema9 > ema21) {
        score += 20;
    }
    // EMA Trend (10 pts max)
    if (ema21 !== null && ema50 !== null && ema21 > ema50) {
        score += 10;
    }

    if (states.volume_regime === "elevated") {
        score += 15;
    } else if (states.volume_regime === "normal") {
        score += 7;
    }

    // RSI (15 pts max)
    if (rsiVal !== null) {
        if (rsiVal > 30 && rsiVal < 70) {
            score += 15;
        } else if (rsiVal >= 25 && rsiVal <= 75) {
            score += 7;
        }
    }

    if (supportZones.length > 0) {
        const closestSupport = Math.max(...supportZones.map(z => z.high));
        const proximity = (currentPrice - closestSupport) / currentPrice;
        if (proximity < 0.01) {
            score += 20;
        } else if (proximity < 0.03) {
            score += 10;
        }
    }

    return Math.min(score, 100);
}

export function confluenceLabel(score: number): string {
    if (score <= 35) return "weak";
    if (score <= 60) return "mixed";
    if (score <= 80) return "favorable";
    return "strong";
}

export function generateSetupCallout(
    states: ReturnType<typeof deriveStates>,
    supportZones: PriceLevel[],
    resistanceZones: PriceLevel[],
    confluenceScore: number,
    currentPrice: number
) {
    const biasLabels: Record<string, string> = {
        "bullish": "Bullish",
        "slightly_bullish": "Cautiously Bullish",
        "neutral": "Neutral",
        "slightly_bearish": "Cautiously Bearish",
        "bearish": "Bearish",
    };
    const biasLabel = biasLabels[states.trend_bias] || "Neutral";

    let longZone: string | null = null;
    if (supportZones.length > 0) {
        const s = supportZones[0];
        longZone = `$${s.low.toLocaleString(undefined, {maximumFractionDigits: 0})}–$${s.high.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
    }

    let tpZone: string | null = null;
    if (resistanceZones.length > 0) {
        const r = resistanceZones[0];
        tpZone = `$${r.low.toLocaleString(undefined, {maximumFractionDigits: 0})}–$${r.high.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
    }

    let invalidation: string | null = null;
    if (supportZones.length >= 2) {
        const inv = supportZones[1].low;
        invalidation = `Below $${inv.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
    } else if (supportZones.length > 0) {
        const inv = supportZones[0].low * 0.99;
        invalidation = `Below $${inv.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
    } else {
        const inv = currentPrice * 0.98;
        invalidation = `Below $${inv.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
    }

    const vwapPhrase = {
        "above": "above VWAP",
        "below": "below VWAP",
        "near": "near VWAP",
    }[states.price_vs_vwap] || "";

    const emaPhrase = {
        "bullish": "EMA alignment is bullish",
        "mixed_bullish": "short-term EMAs turning bullish",
        "mixed_bearish": "short-term EMAs weakening",
        "bearish": "EMA alignment is bearish",
    }[states.ema_alignment] || "EMA alignment is mixed";

    const volPhrase = {
        "elevated": "volume confirming the move",
        "normal": "volume is average",
        "low": "volume is light — treat with caution",
    }[states.volume_regime] || "";

    const summary = `BTC is ${vwapPhrase}. ${emaPhrase}. ${volPhrase}.`.trim().replace(/\s+/g, ' ');

    return {
        bias: biasLabel,
        long_zone: longZone,
        invalidation,
        take_profit_zone: tpZone,
        summary,
        confluence_label: confluenceLabel(confluenceScore),
    };
}


