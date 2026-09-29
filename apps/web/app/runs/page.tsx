'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { getRuns } from '@/lib/api';
import { AgentRun, RunStatus } from '@/lib/types';
import { RunStatusBadge } from '@/components/RunStatusBadge';
import { truncateId, formatDate } from '@/lib/utils';
import { Activity, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

const STATUS_FILTERS: { label: string; value: RunStatus | 'ALL' }[] = [
  { label: 'All', value: 'ALL' },
  { label: 'Running', value: 'RUNNING' },
  { label: 'Success', value: 'SUCCESS' },
  { label: 'Failed', value: 'FAILED' },
  { label: 'Pending', value: 'PENDING' },
  { label: 'Cancelled', value: 'CANCELLED' },
];

export default function RunsPage() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<RunStatus | 'ALL'>('ALL');

  const fetchRuns = useCallback(async (status: RunStatus | 'ALL') => {
    setLoading(true);
    setError(null);
    try {
      const result = await getRuns(1, 20, status === 'ALL' ? undefined : status);
      setRuns(result.runs ?? []);
      setTotal(result.total ?? 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load runs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuns(activeFilter);
  }, [activeFilter, fetchRuns]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Agent Runs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {total} total run{total !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Status filters */}
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setActiveFilter(value)}
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors',
              activeFilter === value
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card text-muted-foreground border-border hover:border-primary/50 hover:text-foreground',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-16 text-muted-foreground">
          <Activity className="h-8 w-8 mx-auto mb-3 animate-pulse opacity-40" />
          <p>Loading runs…</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20 p-6 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      ) : runs.length === 0 ? (
        <div className="rounded-xl border bg-card p-10 text-center text-muted-foreground">
          <Activity className="h-8 w-8 mx-auto mb-3 opacity-40" />
          <p>No runs found{activeFilter !== 'ALL' ? ` with status ${activeFilter}` : ''}.</p>
        </div>
      ) : (
        <div className="rounded-xl border bg-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/30">
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Run ID</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Issue #</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Status</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Iterations</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">PR</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Created</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run, i) => (
                <tr
                  key={run.id}
                  className={cn(
                    'border-b last:border-0 hover:bg-muted/20 transition-colors',
                    i % 2 !== 0 && 'bg-muted/5',
                  )}
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/runs/${run.id}`}
                      className="font-mono text-xs text-primary hover:underline underline-offset-2 flex items-center gap-1"
                    >
                      {truncateId(run.id)}
                      <ExternalLink className="h-3 w-3 opacity-60" />
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">#{run.issue_number}</td>
                  <td className="px-4 py-3">
                    <RunStatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {run.iteration}/{run.max_iterations}
                  </td>
                  <td className="px-4 py-3">
                    {run.pr_url ? (
                      <a
                        href={run.pr_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-green-600 dark:text-green-400 hover:underline flex items-center gap-1"
                      >
                        #{run.pr_number} <ExternalLink className="h-3 w-3 opacity-60" />
                      </a>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {formatDate(run.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
