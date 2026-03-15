'use client';

import { fmtPrice } from '@/lib/indicators';
import { PriceLevel, FibLevel } from '@/lib/indicators';

interface SupportResistanceCardProps {
    currentPrice: number;
    supportZones: PriceLevel[];
    resistanceZones: PriceLevel[];
    fibLevels: FibLevel[];
    sessionHigh: number;
    sessionLow: number;
}

function ZoneRow({
    zone,
    currentPrice,
    type,
}: {
    zone: PriceLevel;
    currentPrice: number;
    type: 'support' | 'resistance';
}) {
    const mid = (zone.low + zone.high) / 2;
    const distPct = ((currentPrice - mid) / currentPrice) * 100;
    const isSupport = type === 'support';

    return (
        <div className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
            <div
                className={`w-1.5 h-8 rounded-full flex-shrink-0 ${isSupport ? 'bg-emerald-400' : 'bg-red-400'
                    }`}
                style={{ opacity: zone.strength }}
            />
            <div className="flex-1 min-w-0">
                <div className="text-sm font-mono text-white">
                    ${zone.low.toLocaleString()} – ${zone.high.toLocaleString()}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                    <div className="h-1 bg-slate-800 rounded-full w-16 overflow-hidden">
                        <div
                            className={`h-full rounded-full ${isSupport ? 'bg-emerald-400' : 'bg-red-400'}`}
                            style={{ width: `${zone.strength * 100}%` }}
                        />
                    </div>
                    <span className="text-xs text-slate-500">{(zone.strength * 100).toFixed(0)}% strength</span>
                </div>
            </div>
            <div className={`text-xs font-mono text-right ${isSupport ? 'text-slate-400' : 'text-slate-400'}`}>
                {distPct > 0 ? `+${distPct.toFixed(2)}%` : `${distPct.toFixed(2)}%`}
            </div>
        </div>
    );
}

export function SupportResistanceCard({
    currentPrice,
    supportZones,
    resistanceZones,
    fibLevels,
    sessionHigh,
    sessionLow,
}: SupportResistanceCardProps) {
    return (
        <div className="rounded-xl border border-white/10 bg-white/5 p-5 space-y-5">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Key Levels</h3>

            {/* Session range */}
            <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-white/5 p-3">
                    <div className="text-xs text-slate-500 mb-1">Session High</div>
                    <div className="text-sm font-mono text-white">{fmtPrice(sessionHigh)}</div>
                </div>
                <div className="rounded-lg bg-white/5 p-3">
                    <div className="text-xs text-slate-500 mb-1">Session Low</div>
                    <div className="text-sm font-mono text-white">{fmtPrice(sessionLow)}</div>
                </div>
            </div>

            {/* Resistance zones */}
            {resistanceZones.length > 0 && (
                <div>
                    <div className="text-xs text-red-400 font-semibold uppercase mb-2 tracking-wider">
                        Resistance
                    </div>
                    {resistanceZones.map((z, i) => (
                        <ZoneRow key={i} zone={z} currentPrice={currentPrice} type="resistance" />
                    ))}
                </div>
            )}

            {/* Current price marker */}
            <div className="flex items-center gap-2 py-1">
                <div className="flex-1 h-px bg-white/20" />
                <span className="text-xs font-mono font-bold text-white bg-white/10 px-2 py-0.5 rounded">
                    {fmtPrice(currentPrice)} ←
                </span>
                <div className="flex-1 h-px bg-white/20" />
            </div>

            {/* Support zones */}
            {supportZones.length > 0 && (
                <div>
                    <div className="text-xs text-emerald-400 font-semibold uppercase mb-2 tracking-wider">
                        Support
                    </div>
                    {supportZones.map((z, i) => (
                        <ZoneRow key={i} zone={z} currentPrice={currentPrice} type="support" />
                    ))}
                </div>
            )}

            {/* Fibonacci levels */}
            {fibLevels.length > 0 && (
                <div>
                    <div className="text-xs text-purple-400 font-semibold uppercase mb-2 tracking-wider">
                        Fibonacci Retracements
                    </div>
                    <div className="space-y-1">
                        {fibLevels.map((f, i) => {
                            const distPct = ((currentPrice - f.price) / currentPrice) * 100;
                            return (
                                <div key={i} className="flex items-center justify-between text-xs">
                                    <span className="text-slate-400 w-12">{f.label}</span>
                                    <span className="font-mono text-white">{fmtPrice(f.price)}</span>
                                    <span className="text-slate-500 w-14 text-right">
                                        {distPct > 0 ? `+${distPct.toFixed(2)}%` : `${distPct.toFixed(2)}%`}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
