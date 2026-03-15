'use client';

import { Candle } from '@/lib/indicators';
import {
    ComposedChart,
    XAxis,
    YAxis,
    Tooltip,
    ReferenceLine,
    ResponsiveContainer,
    Line,
    Bar,
    Cell,
} from 'recharts';
import { format } from 'date-fns';

interface TechnicalChartProps {
    candles: Candle[];
    levels?: {
        support_zones?: { low: number; high: number }[];
        resistance_zones?: { low: number; high: number }[];
        session_high?: number;
        session_low?: number;
    };
}

// Custom candlestick shape rendered as SVG rect
function CandleShape(props: any) {
    const { x, y, width, height, open, close, high, low, index, data } = props;
    const candle = data?.[index];
    if (!candle) return null;

    const isUp = candle.close >= candle.open;
    const color = isUp ? '#34d399' : '#f87171'; // emerald-400 / red-400

    const barWidth = Math.max(width * 0.6, 2);
    const barX = x + (width - barWidth) / 2;

    // Scale helpers — y/height are for the bar chart placeholder; we need chart coords
    // We use the YAxis domain by reading props passed from ComposedChart
    const { yMin, yMax, chartHeight } = props;
    if (yMin == null || yMax == null || chartHeight == null) return null;

    const toY = (price: number) =>
        chartHeight - ((price - yMin) / (yMax - yMin)) * chartHeight;

    const openY = toY(candle.open);
    const closeY = toY(candle.close);
    const highY = toY(candle.high);
    const lowY = toY(candle.low);
    const bodyTop = Math.min(openY, closeY);
    const bodyH = Math.max(Math.abs(closeY - openY), 1);
    const wickX = barX + barWidth / 2;

    return (
        <g>
            {/* High-low wick */}
            <line x1={wickX} x2={wickX} y1={highY} y2={lowY} stroke={color} strokeWidth={1} />
            {/* Body */}
            <rect x={barX} y={bodyTop} width={barWidth} height={bodyH} fill={color} opacity={0.85} />
        </g>
    );
}

// Custom tooltip
function ChartTooltip({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const c = payload[0]?.payload as Candle;
    if (!c) return null;
    const isUp = c.close >= c.open;
    return (
        <div className="bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-xs space-y-1 shadow-xl">
            <div className="text-slate-400">{format(new Date(c.ts), 'MMM d HH:mm')}</div>
            <div className={isUp ? 'text-emerald-400' : 'text-red-400'}>
                O {c.open.toLocaleString()} · H {c.high.toLocaleString()} · L {c.low.toLocaleString()} · C {c.close.toLocaleString()}
            </div>
            {c.vwap != null && <div className="text-purple-400">VWAP {c.vwap.toLocaleString()}</div>}
            {c.ema9 != null && <div className="text-blue-400">EMA9 {c.ema9.toLocaleString()}</div>}
            {c.ema21 != null && <div className="text-yellow-400">EMA21 {c.ema21.toLocaleString()}</div>}
            {c.ema50 != null && <div className="text-orange-400">EMA50 {c.ema50.toLocaleString()}</div>}
        </div>
    );
}

export function TechnicalChart({ candles, levels }: TechnicalChartProps) {
    if (!candles.length) {
        return (
            <div className="h-96 flex items-center justify-center text-slate-500 text-sm">
                No candle data available
            </div>
        );
    }

    // Compute Y domain with padding
    const allPrices = candles.flatMap((c) => [c.high, c.low]);
    const yMin = Math.min(...allPrices) * 0.998;
    const yMax = Math.max(...allPrices) * 1.002;

    // Show last 60 candles max for readability
    const display = candles.slice(-60);

    return (
        <div className="space-y-1">
            {/* Legend */}
            <div className="flex flex-wrap gap-4 text-xs pb-2">
                <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-blue-400 inline-block" /> EMA 9
                </span>
                <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-yellow-400 inline-block" /> EMA 21
                </span>
                <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-orange-400 inline-block" /> EMA 50
                </span>
                <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-purple-400 inline-block rounded" style={{ borderTop: '2px dashed #a78bfa', height: 0 }} /> VWAP
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                    <span className="w-2 h-2 bg-emerald-400/30 border border-emerald-400/50 inline-block rounded-sm" /> Support
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                    <span className="w-2 h-2 bg-red-400/30 border border-red-400/50 inline-block rounded-sm" /> Resistance
                </span>
            </div>

            <ResponsiveContainer width="100%" height={420}>
                <ComposedChart data={display} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                    <XAxis
                        dataKey="ts"
                        tickFormatter={(v) => format(new Date(v), 'HH:mm')}
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        interval={Math.floor(display.length / 6)}
                    />
                    <YAxis
                        domain={[yMin, yMax]}
                        tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={56}
                        orientation="right"
                    />
                    <Tooltip content={<ChartTooltip />} />

                    {/* Support zones */}
                    {levels?.support_zones?.map((z, i) => (
                        <ReferenceLine
                            key={`sup-${i}`}
                            y={z.high}
                            stroke="#34d399"
                            strokeOpacity={0.4}
                            strokeDasharray="3 3"
                        />
                    ))}
                    {/* Resistance zones */}
                    {levels?.resistance_zones?.map((z, i) => (
                        <ReferenceLine
                            key={`res-${i}`}
                            y={z.low}
                            stroke="#f87171"
                            strokeOpacity={0.4}
                            strokeDasharray="3 3"
                        />
                    ))}
                    {/* Session high/low */}
                    {levels?.session_high && (
                        <ReferenceLine y={levels.session_high} stroke="#94a3b8" strokeOpacity={0.3} strokeDasharray="2 4" label={{ value: 'HOD', fill: '#94a3b8', fontSize: 10, position: 'insideTopRight' }} />
                    )}
                    {levels?.session_low && (
                        <ReferenceLine y={levels.session_low} stroke="#94a3b8" strokeOpacity={0.3} strokeDasharray="2 4" label={{ value: 'LOD', fill: '#94a3b8', fontSize: 10, position: 'insideBottomRight' }} />
                    )}

                    {/* VWAP */}
                    <Line dataKey="vwap" stroke="#a78bfa" strokeWidth={1.5} dot={false} strokeDasharray="4 2" connectNulls />
                    {/* EMAs */}
                    <Line dataKey="ema9" stroke="#60a5fa" strokeWidth={1.5} dot={false} connectNulls />
                    <Line dataKey="ema21" stroke="#facc15" strokeWidth={1.5} dot={false} connectNulls />
                    <Line dataKey="ema50" stroke="#fb923c" strokeWidth={1.5} dot={false} connectNulls />

                    {/* Candlestick body — rendered as Bar with custom shape */}
                    <Bar
                        dataKey="close"
                        shape={(props: any) => (
                            <CandleShape
                                {...props}
                                data={display}
                                yMin={yMin}
                                yMax={yMax}
                                chartHeight={420 - 32}
                            />
                        )}
                        isAnimationActive={false}
                    >
                        {display.map((c, i) => (
                            <Cell key={i} fill={c.close >= c.open ? '#34d399' : '#f87171'} />
                        ))}
                    </Bar>
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}
