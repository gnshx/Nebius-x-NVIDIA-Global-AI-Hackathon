'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getRuns, createRun, VERIFIED_RUNS, VERIFIED_REPOSITORIES } from '@/lib/api';
import { AgentRun, RunStatus } from '@/lib/types';
import { RunStatusBadge } from '@/components/RunStatusBadge';
import { truncateId, formatDate } from '@/lib/utils';
import { Activity, ExternalLink, Plus, Sparkles, Play, X, ShieldCheck } from 'lucide-react';
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
  const router = useRouter();
  const [runs, setRuns] = useState<AgentRun[]>(() => VERIFIED_RUNS);
  const [total, setTotal] = useState(() => VERIFIED_RUNS.length);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<RunStatus | 'ALL'>('ALL');

  // Trigger repair modal state
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState('python-humanize/humanize');
  const [issueNumber, setIssueNumber] = useState('466');
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  const handleTriggerRepair = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRepo.trim() || !issueNumber.trim()) return;
    setIsSubmitting(true);
    try {
      const newRun = await createRun({
        repository_full_name: selectedRepo.trim(),
        issue_number: parseInt(issueNumber.trim(), 10) || 1,
      });
      setShowTriggerModal(false);
      router.push(`/runs/${newRun.id}`);
    } catch (err) {
      console.error('Failed to trigger run:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <span>Agent Runs</span>
            <span className="text-xs font-mono font-normal bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              Zero-Hallucination Verified
            </span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {total} total run{total !== 1 ? 's' : ''} • Closed-loop Docker container test battery
          </p>
        </div>

        <button
          onClick={() => setShowTriggerModal(true)}
          className="inline-flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-md shadow-emerald-500/15 active:scale-95"
        >
          <Play className="h-4 w-4 fill-zinc-950" />
          <span>Trigger Open-Source Repair</span>
        </button>
      </div>

      {/* Trigger Modal */}
      {showTriggerModal && (
        <div className="rounded-xl border border-emerald-500/30 bg-card/90 backdrop-blur-md p-5 space-y-4 shadow-xl relative animate-in fade-in-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-foreground">
                Solve Open-Source Issue with RepoMedic
              </h2>
            </div>
            <button
              onClick={() => setShowTriggerModal(false)}
              className="text-muted-foreground hover:text-foreground p-1 rounded-md"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <p className="text-xs text-muted-foreground">
            Select a verified open-source repository or enter any target GitHub repository to trigger the 12-node closed-loop repair pipeline (NVIDIA Nemotron 30B MoE + hermetic sandbox).
          </p>

          <form onSubmit={handleTriggerRepair} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2 space-y-1">
                <label className="text-xs font-medium text-zinc-300">Target Repository</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={selectedRepo}
                    onChange={(e) => setSelectedRepo(e.target.value)}
                    placeholder="e.g. pallets/flask or python-humanize/humanize"
                    className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-zinc-300">GitHub Issue #</label>
                <input
                  type="number"
                  value={issueNumber}
                  onChange={(e) => setIssueNumber(e.target.value)}
                  placeholder="466"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  required
                />
              </div>
            </div>

            {/* Quick-Pick Featured Repos */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-muted-foreground">Quick select:</span>
              <button
                type="button"
                onClick={() => {
                  setSelectedRepo('python-humanize/humanize');
                  setIssueNumber('466');
                }}
                className="px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 transition-colors"
              >
                python-humanize #466
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedRepo('pallets/flask');
                  setIssueNumber('5021');
                }}
                className="px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 transition-colors"
              >
                pallets/flask #5021
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedRepo('psf/requests');
                  setIssueNumber('6122');
                }}
                className="px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 transition-colors"
              >
                psf/requests #6122
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedRepo('tiangolo/fastapi');
                  setIssueNumber('9420');
                }}
                className="px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 transition-colors"
              >
                tiangolo/fastapi #9420
              </button>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-border/50">
              <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>100% Sandbox Pass Required Before PR Dispatch</span>
              </div>
              <button
                type="submit"
                disabled={isSubmitting || !selectedRepo.trim() || !issueNumber.trim()}
                className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-zinc-950 px-5 py-2 rounded-lg text-sm font-semibold transition-all"
              >
                {isSubmitting ? (
                  <>
                    <Activity className="h-4 w-4 animate-spin" />
                    <span>Synthesizing Repair…</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 fill-zinc-950" />
                    <span>Run Autonomous Fix</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

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
