'use client';

import { useState, useEffect } from 'react';
import { Activity, TrendingUp, Calendar, BarChart3, DollarSign, Database } from 'lucide-react';
import { format } from 'date-fns';
import { fetchSentimentIndex, fetchTopDrivers, fetchCurrentPrice } from '@/lib/api';
import { KPICard } from '@/components/kpi-card';
import { SentimentChart } from '@/components/sentiment-chart';
import { TopDrivers } from '@/components/top-drivers';
import { SourcesModal } from '@/components/sources-modal';
import { formatSentiment, getSentimentLabel } from '@/lib/utils';

function DashboardContent() {
  const granularity = 'daily';
  
  const [sentimentData, setSentimentData] = useState<{ data: any[] }>({ data: [] });
  const [priceData, setPriceData] = useState<{ price: number; price_change_24h: number } | null>(null);
  const [driversData, setDriversData] = useState<{ positives: any[], negatives: any[] }>({ 
    positives: [], 
    negatives: [] 
  });
  // Use UTC date for consistency with backend
  const [selectedDate, setSelectedDate] = useState(() => {
    const now = new Date();
    return format(new Date(now.getTime() - now.getTimezoneOffset() * 60000), 'yyyy-MM-dd');
  });
  const [loading, setLoading] = useState(true);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSourcesModalOpen, setIsSourcesModalOpen] = useState(false);
  
  // Fetch sentiment data and price on mount
  useEffect(() => {
    let mounted = true;
    
    async function loadInitialData() {
      try {
        setInitialLoading(true);
        setError(null);
        
        // Load sentiment and price in parallel with timeout
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout - API may be starting up')), 60000)
        );
        
        const dataPromises = Promise.all([
          fetchSentimentIndex(granularity).catch(err => {
            console.error('Failed to fetch sentiment data:', err);
            return { data: [] };
          }),
          fetchCurrentPrice().catch(err => {
            console.error('Failed to fetch price data:', err);
            return null;
          })
        ]);
        
        const [sentiment, price] = await Promise.race([dataPromises, timeoutPromise]) as any;
        
        if (mounted) {
          setSentimentData(sentiment);
          setPriceData(price);
        }
      } catch (error: any) {
        console.error('Failed to load initial data:', error);
        if (mounted) {
          setError(error.message || 'Failed to load data. The API may be starting up (cold start can take 30-60s).');
        }
      } finally {
        if (mounted) {
          setInitialLoading(false);
        }
      }
    }
    
    loadInitialData();
    
    return () => {
      mounted = false;
    };
  }, []);
  
  // Fetch drivers data when date changes
  useEffect(() => {
    async function loadDriversData() {
      setLoading(true);
      try {
        const drivers = await fetchTopDrivers(selectedDate);
        setDriversData(drivers);
      } catch (error) {
        console.error('Failed to fetch drivers data:', error);
        setDriversData({ positives: [], negatives: [] });
      } finally {
        setLoading(false);
      }
    }
    loadDriversData();
  }, [selectedDate]);
  
  // Calculate metrics with proper null checks
  const data = sentimentData.data || [];
  const lastPoint = data.length > 0 ? data[data.length - 1] : null;
  const currentSentiment = lastPoint?.smoothed ?? 0;
  const rawSentiment = lastPoint?.raw ?? 0;
  
  // Calculate 24h change
  const secondLastPoint = data.length >= 2 ? data[data.length - 2] : null;
  const delta24h = (lastPoint?.smoothed != null && secondLastPoint?.smoothed != null)
    ? lastPoint.smoothed - secondLastPoint.smoothed 
    : 0;
  
  // Calculate 7d change
  const lookback7d = Math.min(7, data.length - 1);
  const weekAgoPoint = data.length > lookback7d ? data[data.length - 1 - lookback7d] : null;
  const delta7d = (lastPoint?.smoothed != null && weekAgoPoint?.smoothed != null)
    ? lastPoint.smoothed - weekAgoPoint.smoothed
    : 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8" />
              <div>
                <h1 className="text-3xl font-bold">BTC Market Index</h1>
                <p className="text-muted-foreground">
                  Real-time Bitcoin sentiment from news and social media
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsSourcesModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent transition-colors"
            >
              <Database className="w-4 h-4" />
              <span className="hidden sm:inline">View All Sources</span>
              <span className="sm:hidden">Sources</span>
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Loading State */}
        {initialLoading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
            <p className="text-muted-foreground">Loading dashboard...</p>
            <p className="text-sm text-muted-foreground mt-2">First load may take 30-60s (API cold start)</p>
          </div>
        )}

        {/* Error State */}
        {error && !initialLoading && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mb-8">
            <h3 className="font-semibold text-destructive mb-2">Failed to load data</h3>
            <p className="text-sm text-muted-foreground">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-3 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {/* Dashboard Content */}
        {!initialLoading && (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <KPICard
            title="BTC Price"
            value={priceData ? `$${priceData.price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '...'}
            description={priceData ? `${priceData.price_change_24h >= 0 ? '+' : ''}${priceData.price_change_24h.toFixed(2)}% (24h)` : 'Loading...'}
            delta={priceData?.price_change_24h}
            icon={<DollarSign className="w-4 h-4" />}
          />
          <KPICard
            title="Current Sentiment"
            value={formatSentiment(currentSentiment)}
            description={getSentimentLabel(currentSentiment)}
            icon={<BarChart3 className="w-4 h-4" />}
          />
          <KPICard
            title="Raw Sentiment"
            value={formatSentiment(rawSentiment)}
            icon={<Activity className="w-4 h-4" />}
          />
          <KPICard
            title="24h Change"
            value={formatSentiment(delta24h)}
            delta={delta24h}
            icon={<TrendingUp className="w-4 h-4" />}
          />
          <KPICard
            title="7d Change"
            value={formatSentiment(delta7d)}
            delta={delta7d}
            icon={<Calendar className="w-4 h-4" />}
          />
        </div>

        {/* Sentiment Chart */}
        <div className="rounded-lg border bg-card p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">30-Day Sentiment Trend</h2>
          {data.length === 0 ? (
            <div className="h-[400px] flex items-center justify-center text-muted-foreground">
              No sentiment data available
            </div>
          ) : (
            <SentimentChart data={data} granularity={granularity} />
          )}
        </div>

        {/* Top Drivers */}
        <div className="mb-8">
          <TopDrivers 
            positives={driversData.positives} 
            negatives={driversData.negatives}
            selectedDate={selectedDate}
            onDateChange={setSelectedDate}
            loading={loading}
            availableDates={data.map(d => d.ts)}
          />
        </div>

        {/* Footer Info */}
        <div className="text-center text-sm text-muted-foreground">
          <p>
            Sentiment scores range from -1 (very negative) to +1 (very positive)
          </p>
          <p className="mt-1">
            Data updated hourly via automated pipeline
          </p>
        </div>
        </>
        )}
      </main>

      {/* Sources Modal */}
      <SourcesModal 
        isOpen={isSourcesModalOpen} 
        onClose={() => setIsSourcesModalOpen(false)} 
      />
    </div>
  );
}

export default function Home() {
  return <DashboardContent />;
}
