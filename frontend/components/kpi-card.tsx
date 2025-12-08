import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: number;
  description?: string;
  icon?: React.ReactNode;
}

export function KPICard({ title, value, delta, description, icon }: KPICardProps) {
  const getDeltaColor = (d: number) => {
    if (d > 0) return 'text-green-600 dark:text-green-400';
    if (d < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold">{value}</div>
        {delta !== undefined && (
          <div className={cn('mt-1 text-sm font-medium', getDeltaColor(delta))}>
            {delta >= 0 ? '+' : ''}{delta.toFixed(3)}
            {description && <span className="ml-1 text-muted-foreground">({description})</span>}
          </div>
        )}
      </div>
    </div>
  );
}
