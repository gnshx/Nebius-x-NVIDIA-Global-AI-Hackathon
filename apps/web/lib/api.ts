import { AgentRun, Repository, RunsResponse } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Fetches a paginated list of agent runs, optionally filtered by status.
 */
export async function getRuns(
  page = 1,
  pageSize = 20,
  status?: string,
): Promise<RunsResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (status) params.set('status', status);
  return apiFetch<RunsResponse>(`/api/runs?${params.toString()}`);
}

/**
 * Fetches a single agent run by ID (includes steps).
 */
export async function getRun(id: string): Promise<AgentRun> {
  return apiFetch<AgentRun>(`/api/runs/${id}`);
}

/**
 * Creates a new agent run for a given repository + issue number.
 */
export async function createRun(data: {
  repository_full_name: string;
  issue_number: number;
}): Promise<AgentRun> {
  return apiFetch<AgentRun>('/api/runs', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Cancels a running agent run.
 */
export async function cancelRun(id: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/api/runs/${id}/cancel`, {
    method: 'POST',
  });
}

/**
 * Fetches all registered repositories.
 */
export async function getRepositories(): Promise<Repository[]> {
  return apiFetch<Repository[]>('/api/repositories');
}

/**
 * Registers a new repository by full name (e.g. "owner/repo").
 */
export async function registerRepository(fullName: string): Promise<Repository> {
  return apiFetch<Repository>('/api/repositories', {
    method: 'POST',
    body: JSON.stringify({ full_name: fullName }),
  });
}
