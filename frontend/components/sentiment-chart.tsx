'use client';

import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { format, parseISO } from 'date-fns';
import { SentimentDataPoint } from '@/lib/api';

interface SentimentChartProps {
  data: SentimentDataPoint[];
  granularity: 'hourly' | 'daily';
}

export function SentimentChart({ data, granularity }: SentimentChartProps) {
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      date: parseISO(point.ts),
      timestamp: point.ts,
    }));
  }, [data]);

  const formatXAxis = (timestamp: string) => {
    const date = parseISO(timestamp);
    return granularity === 'hourly' 
      ? format(date, 'MMM d HH:mm')
      : format(date, 'MMM d');
  };

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={formatXAxis}
            className="text-xs"
          />
          <YAxis 
            domain={[-1, 1]} 
            className="text-xs"
            tickFormatter={(value) => value.toFixed(2)}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null;
              const data = payload[0].payload;
              return (
                <div className="rounded-lg border bg-background p-3 shadow-lg">
                  <p className="text-sm font-medium">
                    {format(parseISO(data.timestamp), 'PPp')}
                  </p>
                  <div className="mt-2 space-y-1 text-sm">
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Raw:</span>
                      <span className="font-medium">{data.raw.toFixed(3)}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Smoothed:</span>
                      <span className="font-medium">{data.smoothed.toFixed(3)}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">Posts:</span>
                      <span className="font-medium">{data.n_posts}</span>
                    </div>
                  </div>
                </div>
              );
            }}
          />
          <Legend />
          <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" />
          <Line 
            type="monotone" 
            dataKey="raw" 
            stroke="#94a3b8" 
            strokeWidth={1}
            dot={false}
            name="Raw Sentiment"
            opacity={0.3}
          />
          <Line 
            type="monotone" 
            dataKey="smoothed" 
            stroke="#ef4444" 
            strokeWidth={3}
            dot={false}
            name="Smoothed Sentiment"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
