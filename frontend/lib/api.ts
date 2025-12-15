/**
 * API client for BTC Sentiment Analysis backend
 * 
 * Now uses GitHub Pages static JSON API instead of Render backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://jtron780.github.io/BTC';

export interface SentimentDataPoint {
  ts: string;
  raw: number;
  smoothed: number;
  n_posts: number;
  n_positive: number;
  n_negative: number;
  directional_bias: number;
}

export interface SentimentResponse {
  granularity: string;
  data: SentimentDataPoint[];
}

export interface PriceData {
  price: number;
  price_change_24h: number;
  volume_24h: number;
  last_updated: string;
}

export interface TopDriver {
  title: string;
  polarity: number;
  url: string;
  source: string;
}

export interface TopDriversResponse {
  day: string;
  positives: TopDriver[];
  negatives: TopDriver[];
}

/**
 * Fetch sentiment index data
 */
export async function fetchSentimentIndex(
  granularity: 'hourly' | 'daily' = 'daily'
): Promise<SentimentResponse> {
  const res = await fetch(
    `${API_BASE_URL}/sentiment_${granularity}.json`,
    { cache: 'no-store' }
  );
  
  if (!res.ok) {
    throw new Error(`Failed to fetch sentiment data: ${res.statusText}`);
  }
  
  return res.json();
}

/**
 * Fetch top sentiment drivers for a specific day
 */
export async function fetchTopDrivers(day: string): Promise<TopDriversResponse> {
  const res = await fetch(
    `${API_BASE_URL}/drivers/${day}.json`,
    { cache: 'no-store' }
  );
  
  if (!res.ok) {
    if (res.status === 404) {
      return { day, positives: [], negatives: [] };
    }
    throw new Error(`Failed to fetch top drivers: ${res.statusText}`);
  }
  
  return res.json();
}

/**
 * Fetch current Bitcoin price with 24h change
 */
export async function fetchCurrentPrice(): Promise<PriceData> {
  const response = await fetch(`${API_BASE_URL}/price.json`, {
    cache: 'no-store', // Always get fresh price data
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch price: ${response.statusText}`);
  }
  
  const data: PriceData = await response.json();
  return data;
}

/**
 * Health check (index.json for GitHub Pages)
 */
export async function checkHealth(): Promise<{ status: string; time: string }> {
  const res = await fetch(`${API_BASE_URL}/index.json`, { cache: 'no-store' });
  
  if (!res.ok) {
    throw new Error('API health check failed');
  }
  
  const data = await res.json();
  return { status: 'ok', time: data.updated };
}
