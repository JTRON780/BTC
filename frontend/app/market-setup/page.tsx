'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMarketState, fetchTechnicals, fetchLevels } from '@/lib/api';
import { MarketState, TechnicalsResponse, Levels, Candle } from '@/lib/indicators';
import { MarketSummaryCards } from '@/components/market/MarketSummaryCards';
import { TechnicalChart } from '@/components/market/TechnicalChart';
import { ConfluenceMeter } from '@/components/market/ConfluenceMeter';
import { SupportResistanceCard } from '@/components/market/SupportResistanceCard';
import { SetupCallout } from '@/components/market/SetupCallout';
import { SentimentDivergenceCard } from '@/components/market/SentimentDivergenceCard';
import { RefreshCw, Wifi, WifiOff } from 'lucide-react';

type Timeframe = '1h' | '4h';

const COINBASE_WS = 'wss://advanced-trade-ws.coinbase.com';

export default function MarketSetupPage() {
    const [marketState, setMarketState] = useState<MarketState | null>(null);
    const [technicals, setTechnicals] = useState<TechnicalsResponse | null>(null);
    const [levels, setLevels] = useState<Levels | null>(null);
    const [livePrice, setLivePrice] = useState<number | null>(null);
    const [wsConnected, setWsConnected] = useState(false);
    const [timeframe, setTimeframe] = useState<Timeframe>('1h');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);


    // ── Static data load ──────────────────────────────────────────
    const loadData = useCallback(async (tf: Timeframe) => {
        try {
            setLoading(true);
            setError(null);
            const [ms, tech, lvl] = await Promise.all([
                fetchMarketState().catch(() => null),
                fetchTechnicals(tf === '1h' ? 'hourly' : '4h').catch(() => null),
                fetchLevels().catch(() => null),
            ]);
            setMarketState(ms);
            setTechnicals(tech);
            setLevels(lvl);
            setLastUpdated(new Date());
        } catch (e: any) {
            setError(e.message ?? 'Failed to load data');
        } finally {
            setLoading(false);
        }
    }, []);

    // ── Coinbase WebSocket (live price ticker) ────────────────────
    const connectWS = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const ws = new WebSocket(COINBASE_WS);
        wsRef.current = ws;

        ws.onopen = () => {
            setWsConnected(true);
            ws.send(JSON.stringify({
                type: 'subscribe',
                product_ids: ['BTC-USD'],
                channel: 'ticker',
            }));
        };

        ws.onmessage = (evt) => {
            try {
                const msg = JSON.parse(evt.data);
                if (msg.channel === 'ticker' && msg.events?.[0]?.tickers?.[0]) {
                    const ticker = msg.events[0].tickers[0];
                    const price = parseFloat(ticker.price);
                    if (!isNaN(price) && price > 0) setLivePrice(price);
                }
            } catch { }
        };

        ws.onclose = () => {
            setWsConnected(false);
            // Reconnect after 3s
            reconnectTimeout.current = setTimeout(connectWS, 3000);
        };

        ws.onerror = () => {
            ws.close();
        };
    }, []);

    useEffect(() => {
        loadData(timeframe);
        connectWS();
        return () => {
            clearTimeout(reconnectTimeout.current);
            wsRef.current?.close();
        };
    }, []);

    useEffect(() => {
        loadData(timeframe);
    }, [timeframe]);

    const candles: Candle[] = technicals?.candles ?? [];

    return (
        <div className="min-h-screen bg-[#0a0a0f] text-white">
            {/* Header */}
            <header className="border-b border-white/8 sticky top-0 z-30 backdrop-blur-md bg-[#0a0a0f]/80">
                <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div>
                            <h1 className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                                Market Setup
                            </h1>
                            <p className="text-xs text-slate-500">BTC · Technical Analysis</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Timeframe toggle */}
                        <div className="flex items-center gap-1 bg-white/5 rounded-lg p-1">
                            {(['1h', '4h'] as Timeframe[]).map((tf) => (
                                <button
                                    key={tf}
                                    onClick={() => setTimeframe(tf)}
                                    className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${timeframe === tf
                                        ? 'bg-white/15 text-white'
                                        : 'text-slate-500 hover:text-slate-300'
                                        }`}
                                >
                                    {tf.toUpperCase()}
                                </button>
                            ))}
                        </div>

                        {/* WS status */}
                        <div className="flex items-center gap-1.5 text-xs">
                            {wsConnected ? (
                                <><Wifi className="w-3.5 h-3.5 text-emerald-400" /><span className="text-emerald-400">Live</span></>
                            ) : (
                                <><WifiOff className="w-3.5 h-3.5 text-red-400" /><span className="text-red-400">Disconnected</span></>
                            )}
                        </div>

                        {/* Refresh */}
                        <button
                            onClick={() => loadData(timeframe)}
                            disabled={loading}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                        >
                            <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
                {/* Error */}
                {error && (
                    <div className="rounded-xl border border-red-400/20 bg-red-400/5 p-4 text-sm text-red-400">
                        {error} — data may not have been published yet. Run the pipeline first.
                    </div>
                )}

                {/* Loading skeleton */}
                {loading && !marketState && (
                    <div className="space-y-4 animate-pulse">
                        <div className="grid grid-cols-6 gap-3">
                            {Array.from({ length: 6 }).map((_, i) => (
                                <div key={i} className="h-24 rounded-xl bg-white/5" />
                            ))}
                        </div>
                        <div className="h-96 rounded-xl bg-white/5" />
                    </div>
                )}

                {marketState && (
                    <>
                        {/* Summary cards */}
                        <MarketSummaryCards state={marketState} livePrice={livePrice} />

                        {/* Main content grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Chart — spans 2/3 */}
                            <div className="lg:col-span-2 rounded-xl border border-white/10 bg-white/5 p-5">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                                        Price Chart · {timeframe.toUpperCase()}
                                    </h2>
                                    {livePrice && (
                                        <span className="text-sm font-mono text-white">
                                            ${livePrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                            <span className="inline-block w-1.5 h-1.5 bg-emerald-400 rounded-full ml-2 animate-pulse" />
                                        </span>
                                    )}
                                </div>
                                <TechnicalChart
                                    candles={candles}
                                    levels={levels ?? undefined}
                                />
                            </div>

                            {/* Right column */}
                            <div className="space-y-5">
                                <SetupCallout setup={marketState.setup} regime={marketState.market_regime} />
                                <ConfluenceMeter
                                    score={marketState.confluence_score}
                                    label={marketState.confluence_label}
                                    state={marketState}
                                />
                            </div>
                        </div>

                        {/* Bottom row */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* S/R levels */}
                            {levels && (
                                <SupportResistanceCard
                                    currentPrice={livePrice ?? marketState.price}
                                    supportZones={levels.support_zones}
                                    resistanceZones={levels.resistance_zones}
                                    fibLevels={levels.fibonacci_levels}
                                    sessionHigh={levels.session_high}
                                    sessionLow={levels.session_low}
                                />
                            )}

                            {/* Sentiment divergence */}
                            {marketState.divergence && (
                                <SentimentDivergenceCard
                                    divergence={marketState.divergence}
                                    sentimentRegime={marketState.sentiment_regime}
                                />
                            )}

                            {/* Indicator table */}
                            <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
                                    Indicator Snapshot
                                </h3>
                                <div className="space-y-2">
                                    {[
                                        { label: 'EMA 9', value: marketState.indicators.ema9, color: 'text-blue-400' },
                                        { label: 'EMA 21', value: marketState.indicators.ema21, color: 'text-yellow-400' },
                                        { label: 'EMA 50', value: marketState.indicators.ema50, color: 'text-orange-400' },
                                        { label: 'VWAP', value: marketState.indicators.vwap, color: 'text-purple-400' },
                                        { label: 'RSI 14', value: marketState.indicators.rsi14, color: 'text-white', fmt: (v: number) => v.toFixed(1) },
                                        { label: 'ATR 14', value: marketState.indicators.atr14, color: 'text-slate-300', fmt: (v: number) => `$${v.toFixed(0)}` },
                                    ].map(({ label, value, color, fmt }) => (
                                        <div key={label} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                                            <span className="text-xs text-slate-500">{label}</span>
                                            <span className={`text-sm font-mono font-semibold ${color}`}>
                                                {value == null ? '—' : fmt ? fmt(value) : `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Updated timestamp */}
                                {lastUpdated && (
                                    <p className="text-xs text-slate-600 mt-4 pt-3 border-t border-white/5">
                                        Indicators updated: {lastUpdated.toLocaleTimeString()}
                                    </p>
                                )}
                            </div>
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
