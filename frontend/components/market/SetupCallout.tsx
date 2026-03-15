'use client';

import { SetupCallout as SetupCalloutType } from '@/lib/indicators';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Target, ShieldAlert } from 'lucide-react';

interface SetupCalloutProps {
    setup: SetupCalloutType;
    regime: string;
}

const biasConfig: Record<string, { icon: React.ReactNode; color: string; border: string }> = {
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

export function SetupCallout({ setup, regime }: SetupCalloutProps) {
    const config = biasConfig[setup.bias] ?? biasConfig['Neutral'];

    return (
        <div className={`rounded-xl border ${config.border} bg-white/5 p-5 space-y-4`}>
            {/* Bias header */}
            <div className="flex items-center gap-2">
                {config.icon}
                <div>
                    <div className="text-xs text-slate-500 uppercase tracking-wider">Market Bias</div>
                    <div className={`text-lg font-bold ${config.color}`}>{setup.bias}</div>
                </div>
            </div>

            {/* Summary sentence */}
            <p className="text-sm text-slate-300 leading-relaxed border-l-2 border-white/10 pl-3">
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
