interface TestResultBadgeProps {
  passed?: number;
  failed?: number;
  skipped?: number;
  className?: string;
}

/**
 * Displays inline test result counts with color-coded icons.
 * e.g. ✅ 47 passed  ❌ 2 failed  ⬜ 3 skipped
 */
export function TestResultBadge({ passed, failed, skipped, className }: TestResultBadgeProps) {
  const hasPassed = passed !== undefined && passed !== null;
  const hasFailed = failed !== undefined && failed !== null;
  const hasSkipped = skipped !== undefined && skipped !== null;

  if (!hasPassed && !hasFailed && !hasSkipped) return null;

  return (
    <div className={`flex flex-wrap items-center gap-2 text-sm ${className ?? ''}`}>
      {hasPassed && (
        <span className="flex items-center gap-1 font-medium text-green-600 dark:text-green-400">
          ✅ <span>{passed} passed</span>
        </span>
      )}
      {hasFailed && (
        <span className="flex items-center gap-1 font-medium text-red-600 dark:text-red-400">
          ❌ <span>{failed} failed</span>
        </span>
      )}
      {hasSkipped && (
        <span className="flex items-center gap-1 font-medium text-gray-500 dark:text-gray-400">
          ⬜ <span>{skipped} skipped</span>
        </span>
      )}
    </div>
  );
}
