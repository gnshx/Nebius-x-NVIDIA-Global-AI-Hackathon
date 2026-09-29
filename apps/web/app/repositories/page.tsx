'use client';

import { useEffect, useState } from 'react';
import { getRepositories, registerRepository } from '@/lib/api';
import { Repository } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { Database, Plus, RefreshCw, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

function IndexStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
    indexed: {
      label: 'Indexed',
      icon: <CheckCircle2 className="h-3.5 w-3.5" />,
      cls: 'text-green-700 bg-green-50 dark:bg-green-950/30 dark:text-green-400',
    },
    indexing: {
      label: 'Indexing',
      icon: <RefreshCw className="h-3.5 w-3.5 animate-spin" />,
      cls: 'text-blue-700 bg-blue-50 dark:bg-blue-950/30 dark:text-blue-400',
    },
    pending: {
      label: 'Pending',
      icon: <Clock className="h-3.5 w-3.5" />,
      cls: 'text-yellow-700 bg-yellow-50 dark:bg-yellow-950/30 dark:text-yellow-400',
    },
    failed: {
      label: 'Failed',
      icon: <AlertCircle className="h-3.5 w-3.5" />,
      cls: 'text-red-700 bg-red-50 dark:bg-red-950/30 dark:text-red-400',
    },
  };
  const config = map[status?.toLowerCase()] ?? {
    label: status ?? 'Unknown',
    icon: null,
    cls: 'text-gray-600 bg-gray-100 dark:bg-gray-800',
  };

  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold', config.cls)}>
      {config.icon}
      {config.label}
    </span>
  );
}

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newRepo, setNewRepo] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function fetchRepos() {
    setLoading(true);
    setError(null);
    try {
      const data = await getRepositories();
      setRepos(data ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load repositories');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchRepos();
  }, []);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!newRepo.trim()) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const repo = await registerRepository(newRepo.trim());
      setRepos((prev) => [repo, ...prev]);
      setNewRepo('');
      setShowForm(false);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Failed to register repository');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Repositories</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Registered repositories and their index status
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity"
        >
          <Plus className="h-4 w-4" /> Register Repo
        </button>
      </div>

      {/* Register form */}
      {showForm && (
        <form
          onSubmit={handleRegister}
          className="rounded-xl border bg-card p-4 space-y-3"
        >
          <h2 className="text-sm font-semibold">Register a Repository</h2>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="owner/repository-name"
              value={newRepo}
              onChange={(e) => setNewRepo(e.target.value)}
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              type="submit"
              disabled={submitting || !newRepo.trim()}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 hover:opacity-90 transition-opacity"
            >
              {submitting ? 'Registering…' : 'Register'}
            </button>
          </div>
          {submitError && (
            <p className="text-xs text-red-600 dark:text-red-400">{submitError}</p>
          )}
        </form>
      )}

      {loading ? (
        <div className="text-center py-16 text-muted-foreground">
          <Database className="h-8 w-8 mx-auto mb-3 animate-pulse opacity-40" />
          <p>Loading repositories…</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20 p-6 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      ) : repos.length === 0 ? (
        <div className="rounded-xl border bg-card p-10 text-center text-muted-foreground">
          <Database className="h-8 w-8 mx-auto mb-3 opacity-40" />
          <p>No repositories registered yet.</p>
        </div>
      ) : (
        <div className="rounded-xl border bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/30">
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Repository</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Language</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Branch</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Index Status</th>
                <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Last Indexed</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((repo, i) => (
                <tr
                  key={repo.id}
                  className={cn('border-b last:border-0 hover:bg-muted/20 transition-colors', i % 2 !== 0 && 'bg-muted/5')}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-muted-foreground shrink-0" />
                      <span className="font-medium">{repo.full_name}</span>
                      {repo.private && (
                        <span className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                          Private
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{repo.language ?? '—'}</td>
                  <td className="px-4 py-3">
                    <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                      {repo.default_branch}
                    </code>
                  </td>
                  <td className="px-4 py-3">
                    <IndexStatusBadge status={repo.index_status} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {formatDate(repo.last_indexed_at)}
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
