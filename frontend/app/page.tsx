'use client';

import { useState, useEffect } from 'react';
import { Activity, TrendingUp, Calendar, BarChart3, DollarSign } from 'lucide-react';
import { format } from 'date-fns';
import { fetchSentimentIndex, fetchTopDrivers, fetchCurrentPrice } from '@/lib/api';
import { KPICard } from '@/components/kpi-card';
import { SentimentChart } from '@/components/sentiment-chart';
import { TopDrivers } from '@/components/top-drivers';
import { formatSentiment, getSentimentLabel } from '@/lib/utils';

function DashboardContent() {
  const granularity = 'daily';
  const days = 30;
  
  const [sentimentData, setSentimentData] = useState<{ data: any[] }>({ data: [] });
  const [priceData, setPriceData] = useState<{ price: number; price_change_24h: number } | null>(null);
  const [driversData, setDriversData] = useState<{ positives: any[], negatives: any[] }>({ 
    positives: [], 
    negatives: [] 
  });
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [loading, setLoading] = useState(true);
  
  // Fetch sentiment data and price on mount
  useEffect(() => {
    async function loadSentimentData() {
      try {
        const sentiment = await fetchSentimentIndex(granularity, days);
        setSentimentData(sentiment);
      } catch (error) {
        console.error('Failed to fetch sentiment data:', error);
      }
    }
    
    async function loadPriceData() {
      try {
        const price = await fetchCurrentPrice();
        setPriceData(price);
      } catch (error) {
        console.error('Failed to fetch price data:', error);
      }
    }
    
    loadSentimentData();
    loadPriceData();
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
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8" />
            <div>
              <h1 className="text-3xl font-bold">BTC Market Index</h1>
              <p className="text-muted-foreground">
                Real-time Bitcoin sentiment from news and social media
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
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
      </main>
    </div>
  );
}

export default function Home() {
  return <DashboardContent />;
}
