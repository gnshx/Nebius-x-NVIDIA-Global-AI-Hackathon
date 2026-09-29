'use client';

import { AgentStep, StepType } from '@/lib/types';
import { cn, formatDuration, humanizeStepType } from '@/lib/utils';
import {
  AlertCircle,
  BookOpen,
  Bug,
  CheckCircle2,
  Clock,
  Code2,
  FileCode,
  GitBranch,
  GitPullRequest,
  Globe,
  Loader2,
  Search,
  TestTube,
  Zap,
} from 'lucide-react';
import { StepCard } from './StepCard';
import { RunStatusBadge } from './RunStatusBadge';

interface RunTimelineProps {
  steps: AgentStep[];
  currentIteration: number;
  maxIterations: number;
}

const stepIcons: Record<StepType, React.ReactNode> = {
  issue_analysis: <BookOpen className="h-4 w-4" />,
  repository_analysis: <Search className="h-4 w-4" />,
  code_retrieval: <Code2 className="h-4 w-4" />,
  planning: <GitBranch className="h-4 w-4" />,
  implementation: <FileCode className="h-4 w-4" />,
  test_generation: <TestTube className="h-4 w-4" />,
  sandbox_execution: <Zap className="h-4 w-4" />,
  failure_analysis: <Bug className="h-4 w-4" />,
  web_research: <Globe className="h-4 w-4" />,
  patch_revision: <Code2 className="h-4 w-4" />,
  verification: <CheckCircle2 className="h-4 w-4" />,
  pr_generation: <GitPullRequest className="h-4 w-4" />,
};

function StepStatusIcon({ status }: { status: AgentStep['status'] }) {
  if (status === 'RUNNING') {
    return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
  }
  if (status === 'SUCCESS') {
    return <CheckCircle2 className="h-4 w-4 text-green-500" />;
  }
  if (status === 'FAILED') {
    return <AlertCircle className="h-4 w-4 text-red-500" />;
  }
  if (status === 'SKIPPED') {
    return <Clock className="h-4 w-4 text-gray-400" />;
  }
  // PENDING
  return <Clock className="h-4 w-4 text-yellow-500" />;
}

function stepDotColor(status: AgentStep['status']): string {
  switch (status) {
    case 'RUNNING':
      return 'bg-blue-500 ring-blue-200 dark:ring-blue-900';
    case 'SUCCESS':
      return 'bg-green-500 ring-green-200 dark:ring-green-900';
    case 'FAILED':
      return 'bg-red-500 ring-red-200 dark:ring-red-900';
    case 'SKIPPED':
      return 'bg-gray-300 ring-gray-100 dark:ring-gray-800';
    case 'PENDING':
    default:
      return 'bg-yellow-400 ring-yellow-100 dark:ring-yellow-900';
  }
}

/**
 * Vertical timeline of agent steps grouped by iteration.
 */
export function RunTimeline({ steps, currentIteration, maxIterations }: RunTimelineProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Clock className="h-8 w-8 mx-auto mb-3 opacity-40" />
        <p>No steps recorded yet.</p>
      </div>
    );
  }

  // Group steps by iteration
  const byIteration = steps.reduce<Record<number, AgentStep[]>>((acc, step) => {
    const iter = step.iteration ?? 0;
    if (!acc[iter]) acc[iter] = [];
    acc[iter].push(step);
    return acc;
  }, {});

  const iterations = Object.keys(byIteration)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div className="space-y-6">
      {/* Progress indicator */}
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <div className="flex-1 bg-muted rounded-full h-1.5">
          <div
            className="bg-primary h-1.5 rounded-full transition-all"
            style={{
              width: `${Math.min(100, (currentIteration / maxIterations) * 100)}%`,
            }}
          />
        </div>
        <span className="shrink-0 font-medium">
          Iteration {currentIteration}/{maxIterations}
        </span>
      </div>

      {iterations.map((iter) => (
        <div key={iter}>
          {maxIterations > 1 && (
            <div className="flex items-center gap-2 mb-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2">
                Iteration {iter}
              </span>
              <div className="h-px flex-1 bg-border" />
            </div>
          )}

          <div className="relative">
            {/* Vertical connector line */}
            <div className="absolute left-4 top-5 bottom-5 w-px bg-border" />

            <div className="space-y-1">
              {byIteration[iter].map((step, idx) => {
                const isLast = idx === byIteration[iter].length - 1;
                return (
                  <div key={step.id} className="relative flex gap-4 pl-1">
                    {/* Timeline dot */}
                    <div className="relative z-10 flex items-start pt-3.5">
                      <div
                        className={cn(
                          'h-2.5 w-2.5 rounded-full ring-4 shrink-0 mt-0.5',
                          stepDotColor(step.status),
                        )}
                      />
                    </div>

                    {/* Step card */}
                    <div
                      className={cn(
                        'flex-1 min-w-0 rounded-lg border bg-card px-4 py-3 mb-2',
                        step.status === 'RUNNING' && 'border-blue-300 dark:border-blue-800',
                        step.status === 'FAILED' && 'border-red-300 dark:border-red-800',
                        step.status === 'SUCCESS' && 'border-border',
                      )}
                    >
                      {/* Step header */}
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">
                            {stepIcons[step.step_type] ?? <Code2 className="h-4 w-4" />}
                          </span>
                          <span className="font-medium text-sm">
                            {humanizeStepType(step.step_type)}
                          </span>
                          <RunStatusBadge status={step.status} />
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <StepStatusIcon status={step.status} />
                          {step.duration_seconds !== null && (
                            <span className="font-mono">
                              {formatDuration(step.duration_seconds)}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Expandable details */}
                      <div className="mt-2">
                        <StepCard step={step} isLast={isLast} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
