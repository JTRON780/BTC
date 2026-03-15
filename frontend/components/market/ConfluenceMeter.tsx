'use client';

import { confluenceColor } from '@/lib/indicators';

interface ConfluenceMeterProps {
    score: number;
    label: string;
    state: {
        price_vs_vwap: string;
        ema_alignment: string;
        volume_regime: string;
        sentiment_regime: string;
        indicators: { rsi14: number | null };
    };
}

const signals = [
    { key: 'sentiment', label: 'Sentiment', maxPts: 15 },
    { key: 'vwap', label: 'Price vs VWAP', maxPts: 15 },
    { key: 'ema_cross', label: 'EMA 9 > 21', maxPts: 15 },
    { key: 'ema_trend', label: 'EMA 21 > 50', maxPts: 10 },
    { key: 'volume', label: 'Volume', maxPts: 15 },
    { key: 'rsi', label: 'RSI Neutral Zone', maxPts: 10 },
    { key: 'support', label: 'Near Support', maxPts: 20 },
];

function computeSignalPoints(state: ConfluenceMeterProps['state']): Record<string, number> {
    const pts: Record<string, number> = {};
    const { price_vs_vwap, ema_alignment, volume_regime, sentiment_regime, indicators } = state;

    pts['sentiment'] = ['positive', 'strongly_positive'].includes(sentiment_regime)
        ? 15 : sentiment_regime === 'neutral' ? 7 : 0;
    pts['vwap'] = price_vs_vwap === 'above' ? 15 : price_vs_vwap === 'near' ? 7 : 0;
    pts['ema_cross'] = ['bullish', 'mixed_bullish'].includes(ema_alignment) ? 15 : 0;
    pts['ema_trend'] = ema_alignment === 'bullish' ? 10 : 0;
    pts['volume'] = volume_regime === 'elevated' ? 15 : volume_regime === 'normal' ? 7 : 0;
    const rsi = indicators.rsi14;
    pts['rsi'] = rsi != null ? (rsi > 30 && rsi < 70 ? 10 : rsi > 25 && rsi < 75 ? 5 : 0) : 0;
    // Support proximity — use remaining score gap
    pts['support'] = 0; // filled by backend; shown as 0 when unknown

    return pts;
}

export function ConfluenceMeter({ score, label, state }: ConfluenceMeterProps) {
    const pts = computeSignalPoints(state);
    const color = confluenceColor(score);

    // Radial progress: arc from 0° to score/100 * 270°
    const radius = 52;
    const circumference = Math.PI * radius; // half circle sweep
    const fraction = score / 100;
    const arcLength = fraction * circumference;

    return (
        <div className="rounded-xl border border-white/10 bg-white/5 p-5 flex flex-col gap-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Confluence Score</h3>

            {/* Gauge */}
            <div className="flex flex-col items-center gap-1">
                <svg width="140" height="90" viewBox="0 0 140 90">
                    {/* Track */}
                    <path
                        d="M 10 70 A 60 60 0 0 1 130 70"
                        fill="none"
                        stroke="#1e293b"
                        strokeWidth="10"
                        strokeLinecap="round"
                    />
                    {/* Fill */}
                    <path
                        d="M 10 70 A 60 60 0 0 1 130 70"
                        fill="none"
                        stroke={score >= 75 ? '#34d399' : score >= 55 ? '#facc15' : score >= 35 ? '#fb923c' : '#f87171'}
                        strokeWidth="10"
                        strokeLinecap="round"
                        strokeDasharray={`${arcLength} ${circumference}`}
                        style={{ transition: 'stroke-dasharray 0.6s ease' }}
                    />
                    <text x="70" y="65" textAnchor="middle" className={color} fill="currentColor" fontSize="24" fontWeight="bold">{score}</text>
                    <text x="70" y="79" textAnchor="middle" fill="#64748b" fontSize="11" style={{ textTransform: 'capitalize' }}>{label}</text>
                </svg>
            </div>

            {/* Signal breakdown */}
            <div className="space-y-2">
                {signals.map((sig) => {
                    const earned = pts[sig.key] ?? 0;
                    const pct = (earned / sig.maxPts) * 100;
                    return (
                        <div key={sig.key} className="flex items-center gap-2 text-xs">
                            <div className="w-28 text-slate-400 truncate">{sig.label}</div>
                            <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-500 ${pct >= 100 ? 'bg-emerald-400' : pct > 0 ? 'bg-yellow-400' : 'bg-slate-700'
                                        }`}
                                    style={{ width: `${pct}%` }}
                                />
                            </div>
                            <div className="w-10 text-right text-slate-400">
                                {earned}/{sig.maxPts}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
