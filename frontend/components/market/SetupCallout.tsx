'use client';

import { SetupCallout as SetupCalloutType, EntryQuality } from '@/lib/indicators';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Target, ShieldAlert, CheckCircle2, Zap } from 'lucide-react';

interface SetupCalloutProps {
    setup: SetupCalloutType;
    entryQuality: EntryQuality;
    regime: string;
}

const biasConfig: Record<string, { icon: React.ReactNode; color: string; border: string }> = {
    'Bullish Pullback': {
        icon: <TrendingUp className="w-5 h-5 text-emerald-400" />,
        color: 'text-emerald-400',
        border: 'border-emerald-400/30',
    },
    Bullish: {
        icon: <TrendingUp className="w-5 h-5 text-emerald-400" />,
        color: 'text-emerald-400',
        border: 'border-emerald-400/30',
    },
    'Cautiously Bullish': {
        icon: <TrendingUp className="w-5 h-5 text-yellow-400" />,
        color: 'text-yellow-400',
        border: 'border-yellow-400/30',
    },
    Neutral: {
        icon: <Minus className="w-5 h-5 text-slate-400" />,
        color: 'text-slate-400',
        border: 'border-slate-400/30',
    },
    'Cautiously Bearish': {
        icon: <TrendingDown className="w-5 h-5 text-orange-400" />,
        color: 'text-orange-400',
        border: 'border-orange-400/30',
    },
    Bearish: {
        icon: <TrendingDown className="w-5 h-5 text-red-400" />,
        color: 'text-red-400',
        border: 'border-red-400/30',
    },
};

const entryQualityConfig: Record<string, { icon: React.ReactNode; color: string; border: string }> = {
    'Attractive Long': {
        icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
        color: 'text-emerald-400',
        border: 'border-emerald-400/30',
    },
    'Chase Risk': {
        icon: <Zap className="w-5 h-5 text-orange-400" />,
        color: 'text-orange-400',
        border: 'border-orange-400/30',
    },
    'Neutral': {
        icon: <Minus className="w-5 h-5 text-slate-400" />,
        color: 'text-slate-400',
        border: 'border-slate-400/30',
    },
    'Weak Long': {
        icon: <AlertTriangle className="w-5 h-5 text-yellow-500" />,
        color: 'text-yellow-500',
        border: 'border-yellow-500/30',
    },
    'Avoid': {
        icon: <ShieldAlert className="w-5 h-5 text-red-500" />,
        color: 'text-red-500',
        border: 'border-red-500/30',
    },
};

export function SetupCallout({ setup, entryQuality, regime }: SetupCalloutProps) {
    const config = biasConfig[setup.bias] ?? biasConfig['Neutral'];
    const eqConfig = entryQualityConfig[entryQuality.label] ?? entryQualityConfig['Neutral'];

    return (
        <div className={`rounded-xl border ${config.border} bg-gradient-to-br from-white/5 to-transparent p-6 space-y-5 shadow-lg shadow-black/20`}>
            {/* Flex container to hold Bias and Entry Quality side-by-side or stacked on mobile */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-6 pb-2 border-b border-white/5">
                
                {/* Bias header */}
                <div className="flex items-center gap-3 flex-1">
                    {config.icon}
                    <div>
                        <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Market Bias</div>
                        <div className={`text-lg font-bold ${config.color}`}>{setup.bias}</div>
                    </div>
                </div>

                {/* Entry Quality header */}
                <div className="flex items-center gap-3 flex-1 border-l sm:border-white/10 sm:pl-6 border-transparent pl-0 border-l-0">
                    {eqConfig.icon}
                    <div>
                        <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Entry Quality</div>
                        <div className={`text-lg font-bold ${eqConfig.color}`}>{entryQuality.label}</div>
                    </div>
                </div>

            </div>

            {/* Metrics Breakdown Component (Small tags) */}
            {(entryQuality.distance_to_7d_high !== null || entryQuality.range_position_7d !== null) && (
                <div className="flex flex-wrap gap-2 pt-1">
                    {entryQuality.range_position_7d !== null && (
                        <div className="text-xs px-2 py-1 bg-white/5 rounded-md text-slate-400 border border-white/5 shadow-sm">
                            7d Range Position: <span className="font-mono text-slate-300 ml-1">{(entryQuality.range_position_7d * 100).toFixed(1)}%</span>
                        </div>
                    )}
                    {entryQuality.price_vs_7d_mean !== null && (
                        <div className="text-xs px-2 py-1 bg-white/5 rounded-md text-slate-400 border border-white/5 shadow-sm">
                            vs 7d Mean: <span className={`font-mono ml-1 ${entryQuality.price_vs_7d_mean >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{(entryQuality.price_vs_7d_mean * 100).toFixed(2)}%</span>
                        </div>
                    )}
                    {entryQuality.distance_to_7d_high !== null && (
                        <div className="text-xs px-2 py-1 bg-white/5 rounded-md text-slate-400 border border-white/5 shadow-sm">
                            Distance to 7d High: <span className="font-mono text-slate-300 ml-1">{(entryQuality.distance_to_7d_high * 100).toFixed(2)}%</span>
                        </div>
                    )}
                </div>
            )}

            {/* Summary sentence */}
            <p className="text-sm text-slate-300 leading-relaxed border-l-2 border-indigo-500/30 pl-3">
                {setup.summary}
            </p>

            {/* Setup detail rows */}
            <div className="space-y-3">
                {setup.long_zone && (
                    <div className="flex items-start gap-3">
                        <Target className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                        <div>
                            <div className="text-xs text-slate-500 uppercase">Long Zone</div>
                            <div className="text-sm font-mono text-emerald-400">{setup.long_zone}</div>
                        </div>
                    </div>
                )}

                {setup.take_profit_zone && (
                    <div className="flex items-start gap-3">
                        <TrendingUp className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                        <div>
                            <div className="text-xs text-slate-500 uppercase">Take Profit</div>
                            <div className="text-sm font-mono text-blue-400">{setup.take_profit_zone}</div>
                        </div>
                    </div>
                )}

                <div className="flex items-start gap-3">
                    <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                        <div className="text-xs text-slate-500 uppercase">Invalidation</div>
                        <div className="text-sm font-mono text-red-400">{setup.invalidation}</div>
                    </div>
                </div>
            </div>

            {/* Disclaimer */}
            <p className="text-xs text-slate-600 border-t border-white/5 pt-3">
                Rules-based signals only. Not financial advice.
            </p>
        </div>
    );
}
