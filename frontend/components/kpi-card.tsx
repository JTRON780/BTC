import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: number;
  description?: string;
  icon?: React.ReactNode;
  action?: 'buy' | 'sell' | 'hodl' | null;
}

export function KPICard({ title, value, delta, description, icon, action }: KPICardProps) {
  const getDeltaColor = (d: number) => {
    if (d > 0) return 'text-green-600 dark:text-green-400';
    if (d < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getActionBadge = () => {
    if (action === 'buy') {
      return (
        <span className="inline-block px-3 py-1 bg-green-600/20 text-green-700 dark:text-green-300 rounded-full text-xs font-semibold border border-green-600/30">
          💰 BUY
        </span>
      );
    }
    if (action === 'sell') {
      return (
        <span className="inline-block px-3 py-1 bg-red-600/20 text-red-700 dark:text-red-300 rounded-full text-xs font-semibold border border-red-600/30">
          📊 SELL
        </span>
      );
    }
    if (action === 'hodl') {
      return (
        <span className="inline-block px-3 py-1 bg-blue-600/20 text-blue-700 dark:text-blue-300 rounded-full text-xs font-semibold border border-blue-600/30">
          🔗 HODL
        </span>
      );
    }
    return null;
  };

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
          <div className="mt-3">
            <div className="text-2xl font-bold">{value}</div>
            {delta !== undefined && (
              <div className={cn('mt-1 text-sm font-medium', getDeltaColor(delta))}>
                {delta >= 0 ? '+' : ''}{delta.toFixed(3)}
                {description && <span className="ml-1 text-muted-foreground">({description})</span>}
              </div>
            )}
            {!delta && description && (
              <div className="mt-1 text-sm text-muted-foreground">{description}</div>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          {icon && <div className="text-muted-foreground">{icon}</div>}
          {action && getActionBadge()}
        </div>
      </div>
    </div>
  );
}
