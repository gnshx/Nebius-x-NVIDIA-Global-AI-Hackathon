import Link from 'next/link';
import { getRuns } from '@/lib/api';
import { RunStatusBadge } from '@/components/RunStatusBadge';
import { truncateId, formatDate } from '@/lib/utils';
import { Activity, CheckCircle2, GitPullRequest, Zap, ArrowRight } from 'lucide-react';
import { AgentRun } from '@/lib/types';

async function getStats() {
  try {
    const allRuns = await getRuns(1, 100);
    const runs = allRuns.runs ?? [];
    const total = allRuns.total ?? runs.length;
    const successful = runs.filter((r) => r.status === 'SUCCESS').length;
    const prsCreated = runs.filter((r) => r.pr_url !== null).length;
    const active = runs.filter((r) => r.status === 'RUNNING' || r.status === 'PENDING').length;
    return { total, successful, prsCreated, active, recent: runs.slice(0, 5) };
  } catch {
    return { total: 0, successful: 0, prsCreated: 0, active: 0, recent: [] };
  }
}

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ label, value, icon, color }: StatCardProps) {
  return (
    <div className={`rounded-xl border bg-card p-5 flex items-center gap-4 shadow-sm`}>
      <div className={`rounded-lg p-2.5 ${color}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

export default async function HomePage() {
  const { total, successful, prsCreated, active, recent } = await getStats();

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="text-center space-y-4 py-8">
        <div className="flex justify-center">
          <img src="/assets/logo.jpg" alt="RepoMedic Logo" className="w-20 h-20 rounded-2xl shadow-lg border border-border" />
        </div>
        <h1 className="text-5xl font-extrabold tracking-tight">RepoMedic</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Autonomous GitHub Issue-to-PR Verification Agent
        </p>
        <p className="text-sm text-muted-foreground max-w-xl mx-auto">
          Powered by NVIDIA Nemotron on Nebius Token Factory. Diagnoses bugs, writes patches,
          executes tests in an isolated sandbox, and opens verified pull requests.
        </p>
        <div className="pt-2">
          <Link
            href="/runs"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-lg font-semibold hover:opacity-90 transition-opacity text-sm shadow-md"
          >
            View Active Runs <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Overview</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Runs"
            value={total}
            icon={<Activity className="h-5 w-5 text-blue-600" />}
            color="bg-blue-50 dark:bg-blue-950/30"
          />
          <StatCard
            label="Successful Runs"
            value={successful}
            icon={<CheckCircle2 className="h-5 w-5 text-green-600" />}
            color="bg-green-50 dark:bg-green-950/30"
          />
          <StatCard
            label="PRs Created"
            value={prsCreated}
            icon={<GitPullRequest className="h-5 w-5 text-purple-600" />}
            color="bg-purple-50 dark:bg-purple-950/30"
          />
          <StatCard
            label="Active Runs"
            value={active}
            icon={<Zap className="h-5 w-5 text-yellow-600" />}
            color="bg-yellow-50 dark:bg-yellow-950/30"
          />
        </div>
      </section>

      {/* Recent runs table */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Runs</h2>
          <Link href="/runs" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
            See all <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {recent.length === 0 ? (
          <div className="rounded-xl border bg-card p-8 text-center text-muted-foreground">
            <Activity className="h-8 w-8 mx-auto mb-3 opacity-40" />
            <p>No runs yet. Trigger an agent run via the GitHub webhook or API.</p>
          </div>
        ) : (
          <div className="rounded-xl border bg-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/30">
                  <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Run ID</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Issue #</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Status</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted-foreground">PR</th>
                  <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Created</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((run: AgentRun, i: number) => (
                  <tr
                    key={run.id}
                    className={`border-b last:border-0 hover:bg-muted/20 transition-colors ${
                      i % 2 === 0 ? '' : 'bg-muted/5'
                    }`}
                  >
                    <td className="px-4 py-3">
                      <Link href={`/runs/${run.id}`} className="font-mono text-xs hover:text-primary underline-offset-2 hover:underline">
                        {truncateId(run.id)}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">#{run.issue_number}</td>
                    <td className="px-4 py-3">
                      <RunStatusBadge status={run.status} />
                    </td>
                    <td className="px-4 py-3">
                      {run.pr_url ? (
                        <a
                          href={run.pr_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-green-600 dark:text-green-400 hover:underline"
                        >
                          #{run.pr_number}
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
      </section>

      {/* Architecture Showcase */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">System Architecture</h2>
            <p className="text-sm text-muted-foreground">
              Autonomous execution-and-verification state machine powered by NVIDIA Nemotron & Nebius Token Factory
            </p>
          </div>
        </div>
        <div className="rounded-2xl border bg-card p-2 overflow-hidden shadow-sm">
          <img
            src="/assets/architecture.jpg"
            alt="RepoMedic System Architecture Diagram"
            className="w-full rounded-xl object-cover"
          />
        </div>
      </section>
    </div>
  );
}
