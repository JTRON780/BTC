import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatSentiment(value: number): string {
  return value >= 0 ? `+${value.toFixed(3)}` : value.toFixed(3);
}

export function getSentimentColor(value: number): string {
  if (value > 0.3) return 'text-green-600 dark:text-green-400';
  if (value < -0.3) return 'text-red-600 dark:text-red-400';
  return 'text-yellow-600 dark:text-yellow-400';
}

export function getSentimentLabel(value: number): string {
  if (value > 0.3) return 'Bullish';
  if (value < -0.3) return 'Bearish';
  return 'Neutral';
}
