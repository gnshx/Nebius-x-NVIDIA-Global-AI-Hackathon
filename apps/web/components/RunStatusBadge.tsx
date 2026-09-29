import { RunStatus, StepStatus } from '@/lib/types';
import { cn } from '@/lib/utils';

interface RunStatusBadgeProps {
  status: RunStatus | StepStatus;
  className?: string;
}

const statusConfig: Record<string, { label: string; classes: string }> = {
  RUNNING: {
    label: 'Running',
    classes: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  },
  SUCCESS: {
    label: 'Success',
    classes: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  },
  FAILED: {
    label: 'Failed',
    classes: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  },
  PENDING: {
    label: 'Pending',
    classes: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  },
  CANCELLED: {
    label: 'Cancelled',
    classes: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
  },
  TIMED_OUT: {
    label: 'Timed Out',
    classes: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  },
  SKIPPED: {
    label: 'Skipped',
    classes: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500',
  },
};

export function RunStatusBadge({ status, className }: RunStatusBadgeProps) {
  const config = statusConfig[status] ?? {
    label: status,
    classes: 'bg-gray-100 text-gray-700',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        config.classes,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
