'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { getRun } from '@/lib/api';
import { AgentRun } from '@/lib/types';
import { RunStatusBadge } from '@/components/RunStatusBadge';
import { RunTimeline } from '@/components/RunTimeline';
import { useRunEvents, RunEvent } from '@/hooks/useRunEvents';
import { formatDate, truncateId } from '@/lib/utils';
import {
  ArrowLeft,
  ExternalLink,
  GitPullRequest,
  RefreshCw,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface RunDetailPageProps {
  params: { id: string };
}

export default function RunDetailPage({ params }: RunDetailPageProps) {
  const { id } = params;
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRun = useCallback(async () => {
    try {
      const data = await getRun(id);
      setRun(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load run');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchRun();
  }, [fetchRun]);

  // Handle SSE events for live updates
  const handleEvent = useCallback(
    (event: RunEvent) => {
      // On any relevant event, refetch the run to get the latest state
      if (
        event.type === 'step_started' ||
        event.type === 'step_completed' ||
        event.type === 'run_completed' ||
        event.type === 'run_failed' ||
        event.type === 'step_failed'
      ) {
        fetchRun();
      }
    },
    [fetchRun],
  );

  const isLive = run?.status === 'RUNNING' || run?.status === 'PENDING';
  const { connected } = useRunEvents(isLive ? id : '', handleEvent);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-muted-foreground">
        <RefreshCw className="h-6 w-6 animate-spin mr-2" />
        Loading run…
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="space-y-4">
        <Link href="/runs" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to Runs
        </Link>
        <div className="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20 p-6 text-red-700 dark:text-red-400">
          {error ?? 'Run not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back nav */}
      <Link href="/runs" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground w-fit">
        <ArrowLeft className="h-4 w-4" /> Back to Runs
      </Link>

      {/* Run header card */}
      <div className="rounded-xl border bg-card p-5 space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold">
                Issue #{run.issue_number}
              </h1>
              <RunStatusBadge status={run.status} />
              {isLive && (
                <span
                  className={cn(
                    'inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full',
                    connected
                      ? 'text-green-700 bg-green-50 dark:bg-green-950/30 dark:text-green-400'
                      : 'text-gray-500 bg-gray-100 dark:bg-gray-800',
                  )}
                >
                  {connected ? (
                    <><Wifi className="h-3 w-3" /> Live</>
                  ) : (
                    <><WifiOff className="h-3 w-3" /> Connecting…</>
                  )}
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground font-mono">Run {run.id}</p>
          </div>

          {/* PR link */}
          {run.pr_url && (
            <a
              href={run.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
            >
              <GitPullRequest className="h-4 w-4" />
              View PR #{run.pr_number}
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>

        {/* Iteration progress */}
        <div className="flex flex-wrap gap-6 text-sm">
          <div>
            <span className="text-muted-foreground">Iteration </span>
            <span className="font-semibold">{run.iteration}/{run.max_iterations}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Triggered by </span>
            <span className="font-semibold capitalize">{run.triggered_by}</span>
          </div>
          {run.branch_name && (
            <div>
              <span className="text-muted-foreground">Branch </span>
              <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                {run.branch_name}
              </code>
            </div>
          )}
          {run.started_at && (
            <div>
              <span className="text-muted-foreground">Started </span>
              <span className="font-semibold">{formatDate(run.started_at)}</span>
            </div>
          )}
          {run.completed_at && (
            <div>
              <span className="text-muted-foreground">Completed </span>
              <span className="font-semibold">{formatDate(run.completed_at)}</span>
            </div>
          )}
        </div>

        {/* Error message */}
        {run.error && (
          <div className="rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20 p-3 text-sm text-red-700 dark:text-red-400">
            <span className="font-semibold">Error: </span>{run.error}
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Timeline</h2>
          <button
            onClick={fetchRun}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground border rounded-md px-2.5 py-1.5 hover:bg-muted transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
        <RunTimeline
          steps={run.steps ?? []}
          currentIteration={run.iteration}
          maxIterations={run.max_iterations}
        />
      </div>
    </div>
  );
}
