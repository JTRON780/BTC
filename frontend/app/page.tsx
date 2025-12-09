import { Suspense } from 'react';
import { Activity, TrendingUp, Calendar, BarChart3 } from 'lucide-react';
import { format } from 'date-fns';
import { fetchSentimentIndex, fetchTopDrivers } from '@/lib/api';
import { KPICard } from '@/components/kpi-card';
import { SentimentChart } from '@/components/sentiment-chart';
import { TopDrivers } from '@/components/top-drivers';
import { formatSentiment, getSentimentLabel } from '@/lib/utils';

// Force dynamic rendering
export const dynamic = 'force-dynamic';
export const revalidate = 0;

async function DashboardContent() {
  const granularity = 'daily';
  const days = 30;
  
  // Fetch data with error handling
  let sentimentData: { data: any[] } = { data: [] };
  let driversData: { positives: any[], negatives: any[] } = { positives: [], negatives: [] };
  
  try {
    const [sentiment, drivers] = await Promise.all([
      fetchSentimentIndex(granularity, days),
      fetchTopDrivers(format(new Date(), 'yyyy-MM-dd'))
    ]);
    sentimentData = sentiment;
    driversData = drivers;
  } catch (error) {
    console.error('Failed to fetch data from backend:', error);
    // Continue with empty data rather than crashing
  }
  
  // Calculate metrics with safe null checks
  const data = sentimentData?.data || [];
  const lastItem = data.length > 0 ? data[data.length - 1] : null;
  const secondLastItem = data.length >= 2 ? data[data.length - 2] : null;
  
  const currentSentiment = lastItem?.smoothed ?? 0;
  const rawSentiment = lastItem?.raw ?? 0;
  
  // Calculate 24h change
  const delta24h = (lastItem && secondLastItem) 
    ? (lastItem.smoothed ?? 0) - (secondLastItem.smoothed ?? 0)
    : 0;
  
  // Calculate 7d change
  const lookback7d = Math.min(7, data.length - 1);
  const olderItem = data.length > lookback7d ? data[data.length - 1 - lookback7d] : null;
  const delta7d = (lastItem && olderItem)
    ? (lastItem.smoothed ?? 0) - (olderItem.smoothed ?? 0)
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
          <h2 className="text-xl font-semibold mb-4">
            Top Sentiment Drivers
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              {format(new Date(), 'MMMM d, yyyy')}
            </span>
          </h2>
          <TopDrivers 
            positives={driversData.positives} 
            negatives={driversData.negatives} 
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
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
