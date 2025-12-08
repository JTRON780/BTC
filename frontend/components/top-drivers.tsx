'use client';

import { ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';
import { TopDriver } from '@/lib/api';
import { formatSentiment, getSentimentColor } from '@/lib/utils';

interface TopDriversProps {
  positives: TopDriver[];
  negatives: TopDriver[];
}

export function TopDrivers({ positives, negatives }: TopDriversProps) {
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
    <div className="grid md:grid-cols-2 gap-6">
      {/* Positive Drivers */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
          <h3 className="text-lg font-semibold">Most Positive</h3>
        </div>
        {positives.length === 0 ? (
          <p className="text-sm text-muted-foreground">No positive sentiment drivers found</p>
        ) : (
          <div className="space-y-0">
            {positives.map((driver, idx) => (
              <DriverItem key={idx} driver={driver} index={idx} />
            ))}
          </div>
        )}
      </div>

      {/* Negative Drivers */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
          <h3 className="text-lg font-semibold">Most Negative</h3>
        </div>
        {negatives.length === 0 ? (
          <p className="text-sm text-muted-foreground">No negative sentiment drivers found</p>
        ) : (
          <div className="space-y-0">
            {negatives.map((driver, idx) => (
              <DriverItem key={idx} driver={driver} index={idx} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
