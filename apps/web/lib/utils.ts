import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merges Tailwind classes safely, resolving conflicts.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formats a duration in seconds to a human-readable string.
 * e.g. 83.4 → '1m 23s', 0.8 → '800ms'
 */
export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '—';
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs}s`;
}

/**
 * Returns the first 8 characters of a UUID for display.
 */
export function truncateId(id: string): string {
  return id.slice(0, 8);
}

/**
 * Converts a snake_case step type to a humanized title.
 * e.g. 'issue_analysis' → 'Issue Analysis'
 */
export function humanizeStepType(stepType: string): string {
  return stepType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Formats an ISO date string to a locale date-time string.
 */
export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString();
}
