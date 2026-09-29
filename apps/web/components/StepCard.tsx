'use client';

import { AgentStep } from '@/lib/types';
import { cn } from '@/lib/utils';
import * as Collapsible from '@radix-ui/react-collapsible';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { TestResultBadge } from './TestResultBadge';

interface StepCardProps {
  step: AgentStep;
  isLast?: boolean;
}

/**
 * Expandable card showing all details of an AgentStep including
 * input/output metadata JSON, model used, duration, and errors.
 */
export function StepCard({ step, isLast = false }: StepCardProps) {
  const [open, setOpen] = useState(false);

  const hasContent =
    Object.keys(step.input_metadata ?? {}).length > 0 ||
    Object.keys(step.output_metadata ?? {}).length > 0 ||
    step.model_used ||
    step.error;

  const testPassed =
    typeof step.output_metadata?.tests_passed === 'number'
      ? (step.output_metadata.tests_passed as number)
      : undefined;
  const testFailed =
    typeof step.output_metadata?.tests_failed === 'number'
      ? (step.output_metadata.tests_failed as number)
      : undefined;
  const testSkipped =
    typeof step.output_metadata?.tests_skipped === 'number'
      ? (step.output_metadata.tests_skipped as number)
      : undefined;

  const hasSandboxResults =
    step.step_type === 'sandbox_execution' &&
    (testPassed !== undefined || testFailed !== undefined || testSkipped !== undefined);

  return (
    <Collapsible.Root open={open} onOpenChange={setOpen}>
      <Collapsible.Trigger asChild disabled={!hasContent}>
        <button
          className={cn(
            'w-full flex items-center justify-between text-left py-1 px-2 rounded-md',
            'hover:bg-muted/50 transition-colors text-sm text-muted-foreground',
            !hasContent && 'cursor-default',
          )}
        >
          <div className="flex items-center gap-2">
            {hasContent ? (
              open ? (
                <ChevronDown className="h-3.5 w-3.5 shrink-0" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 shrink-0" />
              )
            ) : (
              <span className="w-3.5" />
            )}
            <span>Details</span>
          </div>
          {hasSandboxResults && (
            <TestResultBadge passed={testPassed} failed={testFailed} skipped={testSkipped} />
          )}
        </button>
      </Collapsible.Trigger>

      <Collapsible.Content className="overflow-hidden data-[state=open]:animate-none">
        <div className="ml-5 mt-2 space-y-3 pb-2">
          {step.model_used && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                Model
              </p>
              <p className="text-xs font-mono text-foreground">{step.model_used}</p>
            </div>
          )}

          {step.error && (
            <div>
              <p className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-1">
                Error
              </p>
              <pre className="text-xs bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 p-2 rounded border border-red-200 dark:border-red-900 overflow-x-auto whitespace-pre-wrap break-all">
                {step.error}
              </pre>
            </div>
          )}

          {Object.keys(step.input_metadata ?? {}).length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                Input
              </p>
              <pre className="text-xs bg-muted p-2 rounded border border-border overflow-x-auto whitespace-pre-wrap break-all">
                {JSON.stringify(step.input_metadata, null, 2)}
              </pre>
            </div>
          )}

          {Object.keys(step.output_metadata ?? {}).length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                Output
              </p>
              <pre className="text-xs bg-muted p-2 rounded border border-border overflow-x-auto whitespace-pre-wrap break-all">
                {JSON.stringify(step.output_metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </Collapsible.Content>
    </Collapsible.Root>
  );
}
