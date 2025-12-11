'use client';

import { ExternalLink, TrendingUp, TrendingDown, Calendar as CalendarIcon, Filter } from 'lucide-react';
import { format, parseISO, subDays } from 'date-fns';
import { useState, useMemo } from 'react';
import { TopDriver } from '@/lib/api';
import { formatSentiment, getSentimentColor } from '@/lib/utils';

interface TopDriversProps {
  positives: TopDriver[];
  negatives: TopDriver[];
  selectedDate: string;
  onDateChange: (date: string) => void;
  selectedSource: string;
  onSourceChange: (source: string) => void;
  loading?: boolean;
  availableDates: string[];
}

export function TopDrivers({ 
  positives, 
  negatives, 
  selectedDate, 
  onDateChange,
  selectedSource,
  onSourceChange,
  loading = false,
  availableDates 
}: TopDriversProps) {
  // Generate date options from the last 30 days (using UTC for consistency with backend)
  const dateOptions = Array.from({ length: 30 }, (_, i) => {
    const now = new Date();
    const utcDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    const date = subDays(utcDate, i);
    return format(date, 'yyyy-MM-dd');
  });

  // Get unique sources from both positive and negative drivers
  const allSources = useMemo(() => {
    const sources = new Set<string>();
    positives.forEach(d => sources.add(d.source));
    negatives.forEach(d => sources.add(d.source));
    return Array.from(sources).sort();
  }, [positives, negatives]);

  // Filter drivers by selected source
  const filteredPositives = useMemo(() => {
    if (selectedSource === 'all') return positives;
    return positives.filter(d => d.source === selectedSource);
  }, [positives, selectedSource]);

  const filteredNegatives = useMemo(() => {
    if (selectedSource === 'all') return negatives;
    return negatives.filter(d => d.source === selectedSource);
  }, [negatives, selectedSource]);

  const DriverItem = ({ driver, index }: { driver: TopDriver; index: number }) => (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <div className="flex-shrink-0 w-6 text-sm font-medium text-muted-foreground">
        {index + 1}.
      </div>
      <div className="flex-1 min-w-0">
        <a 
          href={driver.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-sm font-medium hover:underline line-clamp-2 flex items-start gap-1"
        >
          {driver.title}
          <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
        </a>
        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
          <span className={getSentimentColor(driver.polarity)}>
            {formatSentiment(driver.polarity)}
          </span>
          <span>•</span>
          <span className="capitalize">{driver.source}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      {/* Header with Date and Source Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h2 className="text-xl font-semibold">Top Sentiment Drivers</h2>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          {/* Date Picker */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-primary/30 bg-primary/5 hover:bg-primary/10 transition-colors">
            <CalendarIcon className="w-4 h-4 text-primary" />
            <select
              value={selectedDate}
              onChange={(e) => onDateChange(e.target.value)}
              className="text-sm bg-transparent focus:outline-none font-medium"
            >
              {dateOptions.map((date) => (
                <option key={date} value={date}>
                  {format(parseISO(date), 'MMMM d, yyyy')}
                </option>
              ))}
            </select>
          </div>
          
          {/* Source Filter */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-blue-500/30 bg-blue-500/5 hover:bg-blue-500/10 transition-colors">
            <Filter className="w-4 h-4 text-blue-500" />
            <select
              value={selectedSource}
              onChange={(e) => onSourceChange(e.target.value)}
              className="text-sm bg-transparent focus:outline-none font-medium"
            >
              <option value="all">All Sources</option>
              {allSources.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Drivers Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Positive Drivers */}
          <div className="rounded-lg border bg-card p-6 flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
              <h3 className="text-lg font-semibold">Most Positive</h3>
              <span className="text-xs text-muted-foreground ml-auto">({filteredPositives.length})</span>
            </div>
            {filteredPositives.length === 0 ? (
              <p className="text-sm text-muted-foreground">No positive sentiment drivers found</p>
            ) : (
              <div className="space-y-0 overflow-y-auto max-h-[500px] pr-2 scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent">
                {filteredPositives.map((driver, idx) => (
                  <DriverItem key={idx} driver={driver} index={idx} />
                ))}
              </div>
            )}
          </div>

          {/* Negative Drivers */}
          <div className="rounded-lg border bg-card p-6 flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
              <h3 className="text-lg font-semibold">Most Negative</h3>
              <span className="text-xs text-muted-foreground ml-auto">({filteredNegatives.length})</span>
            </div>
            {filteredNegatives.length === 0 ? (
              <p className="text-sm text-muted-foreground">No negative sentiment drivers found</p>
            ) : (
              <div className="space-y-0 overflow-y-auto max-h-[500px] pr-2 scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent">
                {filteredNegatives.map((driver, idx) => (
                  <DriverItem key={idx} driver={driver} index={idx} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

