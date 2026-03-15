'use client';

import { MarketState } from '@/lib/indicators';
import { fmtPrice, confluenceColor } from '@/lib/indicators';
import { RegimeBadge } from './RegimeBadge';
import { TrendingUp, TrendingDown, Minus, Activity, BarChart3, Zap } from 'lucide-react';

interface MarketSummaryCardsProps {
    state: MarketState;
    livePrice: number | null;
}

function Card({
    title,
    children,
    icon,
}: {
    title: string;
    children: React.ReactNode;
    icon: React.ReactNode;
}) {
    return (
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-medium uppercase tracking-wider">
                <span>{title}</span>
                <span className="opacity-60">{icon}</span>
            </div>
            {children}
        </div>
    );
}

export function MarketSummaryCards({ state, livePrice }: MarketSummaryCardsProps) {
    const price = livePrice ?? state.price;
    const vwap = state.indicators.vwap;
    const vwapDiff = vwap ? ((price - vwap) / vwap) * 100 : null;

    // EMA alignment label
    const emaLabels: Record<string, string> = {
        bullish: '9 > 21 > 50 ✓',
        bearish: '9 < 21 < 50 ✗',
        mixed_bullish: '9 > 21 (partial)',
        mixed_bearish: '9 < 21 (partial)',
        unknown: '—',
    };

    const vwapIcon =
        state.price_vs_vwap === 'above' ? (
            <TrendingUp className="w-3 h-3 text-emerald-400" />
        ) : state.price_vs_vwap === 'below' ? (
            <TrendingDown className="w-3 h-3 text-red-400" />
        ) : (
            <Minus className="w-3 h-3 text-yellow-400" />
        );

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {/* Live Price */}
            <Card title="BTC Price" icon={<Activity className="w-3.5 h-3.5" />}>
                <div className="text-2xl font-bold text-white tabular-nums">
                    {fmtPrice(price)}
                </div>
                <div className="flex items-center gap-1">
                    <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-xs text-slate-400">Live</span>
                </div>
            </Card>

            {/* Market Regime */}
            <Card title="Market Regime" icon={<BarChart3 className="w-3.5 h-3.5" />}>
                <RegimeBadge regime={state.market_regime} size="sm" />
                <span className="text-xs text-slate-400 capitalize">{state.trend_bias.replace('_', ' ')}</span>
            </Card>

            {/* Confluence */}
            <Card title="Confluence" icon={<Zap className="w-3.5 h-3.5" />}>
                <div className={`text-2xl font-bold tabular-nums ${confluenceColor(state.confluence_score)}`}>
                    {state.confluence_score}
                    <span className="text-sm text-slate-400 font-normal ml-1">/ 100</span>
                </div>
                <span className="text-xs text-slate-400 capitalize">{state.confluence_label}</span>
            </Card>

            {/* VWAP Distance */}
            <Card title="vs VWAP" icon={vwapIcon}>
                <div className={`text-xl font-bold tabular-nums ${state.price_vs_vwap === 'above' ? 'text-emerald-400' :
                        state.price_vs_vwap === 'below' ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                    {vwapDiff != null ? `${vwapDiff > 0 ? '+' : ''}${vwapDiff.toFixed(2)}%` : '—'}
                </div>
                <span className="text-xs text-slate-400">{fmtPrice(vwap)}</span>
            </Card>

            {/* EMA State */}
            <Card title="EMA Alignment" icon={<TrendingUp className="w-3.5 h-3.5" />}>
                <div className={`text-sm font-semibold ${state.ema_alignment === 'bullish' ? 'text-emerald-400' :
                        state.ema_alignment === 'bearish' ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                    {emaLabels[state.ema_alignment] ?? state.ema_alignment}
                </div>
                <div className="text-xs text-slate-400 flex flex-col gap-0.5">
                    <span>EMA9 {fmtPrice(state.indicators.ema9)}</span>
                    <span>EMA21 {fmtPrice(state.indicators.ema21)}</span>
                </div>
            </Card>

            {/* RSI */}
            <Card title="RSI 14" icon={<BarChart3 className="w-3.5 h-3.5" />}>
                <div className={`text-2xl font-bold tabular-nums ${state.indicators.rsi14 == null ? 'text-slate-400' :
                        state.indicators.rsi14 > 70 ? 'text-red-400' :
                            state.indicators.rsi14 < 30 ? 'text-emerald-400' : 'text-white'
                    }`}>
                    {state.indicators.rsi14?.toFixed(1) ?? '—'}
                </div>
                <span className="text-xs text-slate-400">
                    {state.indicators.rsi14 == null ? '' :
                        state.indicators.rsi14 > 70 ? 'Overbought' :
                            state.indicators.rsi14 < 30 ? 'Oversold' : 'Neutral'}
                </span>
            </Card>
        </div>
    );
}
