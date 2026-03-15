'use client';

import { TrendingUp, TrendingDown, Minus, Volume2, AlertCircle } from 'lucide-react';

interface Divergence {
    type: string;
    price_change_24h_pct: number;
    sentiment_change_24h: number | null;
    volume_confirming: boolean;
    headline: string;
    detail: string;
    signal: 'bullish' | 'bearish' | 'neutral';
}

interface SentimentDivergenceCardProps {
    divergence: Divergence;
    sentimentRegime: string;
}

const signalConfig = {
    bullish: {
        icon: <TrendingUp className="w-5 h-5 text-emerald-400" />,
        border: 'border-emerald-400/30',
        bg: 'bg-emerald-400/5',
        badge: 'bg-emerald-400/15 text-emerald-400',
        label: 'Bullish Signal',
    },
    bearish: {
        icon: <TrendingDown className="w-5 h-5 text-red-400" />,
        border: 'border-red-400/30',
        bg: 'bg-red-400/5',
        badge: 'bg-red-400/15 text-red-400',
        label: 'Bearish Signal',
    },
    neutral: {
        icon: <Minus className="w-5 h-5 text-slate-400" />,
        border: 'border-white/10',
        bg: 'bg-white/5',
        badge: 'bg-slate-400/15 text-slate-400',
        label: 'Neutral',
    },
};

const sentimentEmoji: Record<string, string> = {
    strongly_positive: '🟢 Strongly Positive',
    positive: '🟢 Positive',
    neutral: '⚪ Neutral',
    negative: '🔴 Negative',
    strongly_negative: '🔴 Strongly Negative',
};

function StatBox({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
    return (
        <div className="rounded-lg bg-white/5 p-3 flex flex-col gap-1">
            <span className="text-xs text-slate-500">{label}</span>
            <span className={`text-sm font-mono font-semibold ${color ?? 'text-white'}`}>{value}</span>
            {sub && <span className="text-xs text-slate-600">{sub}</span>}
        </div>
    );
}

export function SentimentDivergenceCard({ divergence, sentimentRegime }: SentimentDivergenceCardProps) {
    const cfg = signalConfig[divergence.signal];

    const priceColor =
        divergence.price_change_24h_pct > 0
            ? 'text-emerald-400'
            : divergence.price_change_24h_pct < 0
                ? 'text-red-400'
                : 'text-slate-400';

    const sentColor =
        divergence.sentiment_change_24h != null
            ? divergence.sentiment_change_24h > 0
                ? 'text-emerald-400'
                : divergence.sentiment_change_24h < 0
                    ? 'text-red-400'
                    : 'text-slate-400'
            : 'text-slate-500';

    return (
        <div className={`rounded-xl border ${cfg.border} ${cfg.bg} p-5 space-y-4`}>
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
                <div>
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                        Sentiment vs Price
                    </h3>
                    <div className="flex items-center gap-2">
                        {cfg.icon}
                        <span className="text-base font-semibold text-white">{divergence.headline}</span>
                    </div>
                </div>
                <span className={`text-xs font-semibold px-2 py-1 rounded-full whitespace-nowrap ${cfg.badge}`}>
                    {cfg.label}
                </span>
            </div>

            {/* Detail paragraph */}
            <p className="text-sm text-slate-400 leading-relaxed border-l-2 border-white/10 pl-3">
                {divergence.detail}
            </p>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-2">
                <StatBox
                    label="Price 24h"
                    value={`${divergence.price_change_24h_pct > 0 ? '+' : ''}${divergence.price_change_24h_pct.toFixed(2)}%`}
                    color={priceColor}
                />
                <StatBox
                    label="Sentiment Δ"
                    value={
                        divergence.sentiment_change_24h != null
                            ? `${divergence.sentiment_change_24h > 0 ? '+' : ''}${divergence.sentiment_change_24h.toFixed(3)}`
                            : '—'
                    }
                    sub="daily smoothed"
                    color={sentColor}
                />
                <StatBox
                    label="Volume"
                    value={divergence.volume_confirming ? 'Confirming' : 'Light'}
                    sub={divergence.volume_confirming ? 'above avg' : 'below avg'}
                    color={divergence.volume_confirming ? 'text-emerald-400' : 'text-orange-400'}
                />
            </div>

            {/* Sentiment regime */}
            <div className="flex items-center justify-between pt-1 border-t border-white/5 text-xs">
                <span className="text-slate-500">Current sentiment regime</span>
                <span className="text-slate-300">{sentimentEmoji[sentimentRegime] ?? sentimentRegime}</span>
            </div>
        </div>
    );
}
