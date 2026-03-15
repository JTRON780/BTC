'use client';

import { regimeConfig } from '@/lib/indicators';

interface RegimeBadgeProps {
    regime: string;
    size?: 'sm' | 'md' | 'lg';
}

export function RegimeBadge({ regime, size = 'md' }: RegimeBadgeProps) {
    const config = regimeConfig(regime);
    const sizeClass = {
        sm: 'text-xs px-2 py-0.5',
        md: 'text-sm px-3 py-1',
        lg: 'text-base px-4 py-1.5',
    }[size];

    return (
        <span
            className={`inline-flex items-center font-semibold rounded-full border ${config.bg} ${config.color} ${sizeClass}`}
        >
            {config.label}
        </span>
    );
}
