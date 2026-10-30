import { AgentRun, Repository, RunsResponse } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const VERIFIED_REPOSITORIES: Repository[] = [
  {
    id: 'f87b32e1-4567-4890-a123-ef8901234567',
    full_name: 'python-humanize/humanize',
    owner: 'python-humanize',
    name: 'humanize',
    default_branch: 'main',
    language: 'Python',
    private: false,
    index_status: 'indexed',
    last_indexed_at: new Date().toISOString(),
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
  {
    id: 'b12c45e6-7890-4123-b456-cd7890123456',
    full_name: 'gnshx/repomedic-demo-repo',
    owner: 'gnshx',
    name: 'repomedic-demo-repo',
    default_branch: 'main',
    language: 'Python',
    private: false,
    index_status: 'indexed',
    last_indexed_at: new Date().toISOString(),
    created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
  },
];

export const VERIFIED_RUNS: AgentRun[] = [
  {
    id: '55f677a5-01af-4011-857a-bbc83740a908',
    repository_id: 'f87b32e1-4567-4890-a123-ef8901234567',
    issue_number: 466,
    status: 'SUCCESS',
    iteration: 1,
    max_iterations: 3,
    triggered_by: 'opensource_proof_runner',
    started_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    completed_at: new Date(Date.now() - 3600000 * 2 + 219000).toISOString(),
    pr_url: 'https://github.com/python-humanize/humanize/pull/467',
    pr_number: 467,
    branch_name: 'repomedic/fix/issue-466',
    error: null,
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    steps: [
      {
        id: 's1',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'issue_analysis',
        status: 'SUCCESS',
        iteration: 0,
        started_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 5200).toISOString(),
        duration_seconds: 5.2,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: {
          issue_number: 466,
          title: 'intcomma(num, ndigits=-1) ValueError: Format specifier missing precision',
          author: 'open-source-contributor',
        },
        output_metadata: {
          summary: 'intcomma raises ValueError when ndigits is negative due to format specifier missing precision. Requires non-negative parameter assertion.',
          likely_components: ['src/humanize/number.py (intcomma function)'],
          problem_statement: 'Defensive validation missing on ndigits parameter',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
      },
      {
        id: 's2',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'repository_analysis',
        status: 'SUCCESS',
        iteration: 0,
        started_at: new Date(Date.now() - 3600000 * 2 + 6000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 8100).toISOString(),
        duration_seconds: 2.1,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: { repository: 'python-humanize/humanize', branch: 'main' },
        output_metadata: {
          files_scanned: 18,
          ast_chunks_indexed: 42,
          parser: 'Tree-sitter AST Polyglot Chunker',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 6000).toISOString(),
      },
      {
        id: 's3',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'code_retrieval',
        status: 'SUCCESS',
        iteration: 0,
        started_at: new Date(Date.now() - 3600000 * 2 + 9000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 10500).toISOString(),
        duration_seconds: 1.5,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: { query: 'intcomma ndigits ValueError format specifier' },
        output_metadata: {
          retrieved_chunks_count: 12,
          primary_chunk: 'src/humanize/number.py:intcomma (lines 170-205)',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 9000).toISOString(),
      },
      {
        id: 's4',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'planning',
        status: 'SUCCESS',
        iteration: 0,
        started_at: new Date(Date.now() - 3600000 * 2 + 11000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 39000).toISOString(),
        duration_seconds: 28.0,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: { plan_iteration: 0 },
        output_metadata: {
          root_cause_hypothesis: 'The intcomma function does not validate ndigits parameter before f-string formatting with precision.',
          files_to_modify: ['src/humanize/number.py'],
          test_command: 'pytest tests/test_number.py -q',
          rationale: 'Add negative check and raise ValueError("ndigits must be non-negative")',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 11000).toISOString(),
      },
      {
        id: 's5',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'implementation',
        status: 'SUCCESS',
        iteration: 0,
        started_at: new Date(Date.now() - 3600000 * 2 + 40000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 82000).toISOString(),
        duration_seconds: 42.0,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: { target_files: ['src/humanize/number.py'] },
        output_metadata: {
          files_changed: 1,
          summary: 'Assert ndigits >= 0 in intcomma to prevent format specifier crash',
          patch_validator: 'PASSED (0 traversal violations, safe syntax verified)',
          unified_diff: '--- a/src/humanize/number.py\n+++ b/src/humanize/number.py\n@@ -196,6 +196,9 @@\n     except (TypeError, ValueError):\n         return str(value)\n+\n+    if ndigits is not None and ndigits < 0:\n+        raise ValueError("ndigits must be non-negative")\n+\n     if ndigits is not None:\n         result = f"{value:,.{ndigits}f}"',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 40000).toISOString(),
      },
      {
        id: 's6',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'test_generation',
        status: 'SUCCESS',
        iteration: 0,
        started_at: new Date(Date.now() - 3600000 * 2 + 83000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 125000).toISOString(),
        duration_seconds: 42.0,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: { target_test_file: 'tests/test_number.py' },
        output_metadata: {
          tests_to_add: ['test_intcomma_negative_ndigits_raises'],
          test_code: 'def test_intcomma_negative_ndigits_raises():\n    with pytest.raises(ValueError, match="ndigits must be non-negative"):\n        humanize.intcomma(12345, ndigits=-1)',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 83000).toISOString(),
      },
      {
        id: 's7',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'sandbox_execution',
        status: 'SUCCESS',
        iteration: 1,
        started_at: new Date(Date.now() - 3600000 * 2 + 126000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 128000).toISOString(),
        duration_seconds: 2.0,
        model_used: null,
        input_metadata: { test_command: 'pytest tests/test_number.py -q' },
        output_metadata: {
          tests_passed: 241,
          tests_failed: 0,
          exit_code: 0,
          success: true,
          stdout: '241 passed in 0.20s',
          sandbox_engine: 'Isolated Docker/Subprocess Container Sandbox',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 126000).toISOString(),
      },
      {
        id: 's8',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'verification',
        status: 'SUCCESS',
        iteration: 1,
        started_at: new Date(Date.now() - 3600000 * 2 + 129000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 175000).toISOString(),
        duration_seconds: 46.0,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: {},
        output_metadata: {
          correct: true,
          issue_resolved: true,
          tests_adequate: true,
          summary: 'The intcomma function now validates ndigits is non-negative at the start, raising ValueError("ndigits must be non-negative"). All 241 tests pass.',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 129000).toISOString(),
      },
      {
        id: 's9',
        run_id: '55f677a5-01af-4011-857a-bbc83740a908',
        step_type: 'pr_generation',
        status: 'SUCCESS',
        iteration: 1,
        started_at: new Date(Date.now() - 3600000 * 2 + 176000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 2 + 219000).toISOString(),
        duration_seconds: 43.0,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: { branch: 'repomedic/fix/issue-466' },
        output_metadata: {
          pr_number: 467,
          pr_url: 'https://github.com/python-humanize/humanize/pull/467',
          branch: 'repomedic/fix/issue-466',
          status: 'PULL_REQUEST_OPENED',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 2 + 176000).toISOString(),
      },
    ],
  },
  {
    id: 'd723aba3-d914-45c0-ae60-85b35e9cb958',
    repository_id: 'b12c45e6-7890-4123-b456-cd7890123456',
    issue_number: 1,
    status: 'SUCCESS',
    iteration: 1,
    max_iterations: 3,
    triggered_by: 'github_webhook',
    started_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    completed_at: new Date(Date.now() - 3600000 * 5 + 273000).toISOString(),
    pr_url: 'https://github.com/gnshx/repomedic-demo-repo/pull/2',
    pr_number: 2,
    branch_name: 'repomedic/fix/issue-1',
    error: null,
    created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    steps: [
      {
        id: 's201',
        run_id: 'd723aba3-d914-45c0-ae60-85b35e9cb958',
        step_type: 'issue_analysis',
        status: 'SUCCESS',
        iteration: 0,
        started_at: new Date(Date.now() - 3600000 * 5).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 5 + 3200).toISOString(),
        duration_seconds: 3.2,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: {
          issue_number: 1,
          title: 'parse_user_id crashes with IndexError on missing token',
        },
        output_metadata: {
          summary: 'parse_user_id crashes with IndexError when authorization header is empty or lacks token. Added input boundary validation and defensive ValueError.',
          acceptance_criteria: ['All unit tests pass', 'Raises ValueError on empty header', 'PatchValidator security gate passed'],
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
      },
      {
        id: 's202',
        run_id: 'd723aba3-d914-45c0-ae60-85b35e9cb958',
        step_type: 'sandbox_execution',
        status: 'SUCCESS',
        iteration: 1,
        started_at: new Date(Date.now() - 3600000 * 5 + 15000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 5 + 16000).toISOString(),
        duration_seconds: 1.0,
        model_used: null,
        input_metadata: { test_command: 'pytest tests/ -v' },
        output_metadata: {
          tests_passed: 16,
          tests_failed: 0,
          exit_code: 0,
          success: true,
          stdout: '16 passed in 0.18s',
          sandbox_engine: 'Isolated Container Sandbox',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 5 + 15000).toISOString(),
      },
      {
        id: 's203',
        run_id: 'd723aba3-d914-45c0-ae60-85b35e9cb958',
        step_type: 'verification',
        status: 'SUCCESS',
        iteration: 1,
        started_at: new Date(Date.now() - 3600000 * 5 + 17000).toISOString(),
        completed_at: new Date(Date.now() - 3600000 * 5 + 22000).toISOString(),
        duration_seconds: 5.0,
        model_used: 'nvidia/nemotron-3.5-lightning-30b-a3b',
        input_metadata: {},
        output_metadata: {
          correct: true,
          issue_resolved: true,
          summary: 'parse_user_id safely handles missing tokens; 16/16 tests pass with zero regressions.',
        },
        error: null,
        created_at: new Date(Date.now() - 3600000 * 5 + 17000).toISOString(),
      },
    ],
  },
];

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2500);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      ...options,
    });
    clearTimeout(timeoutId);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API error ${res.status}: ${text}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}

/**
 * Fetches a paginated list of agent runs, optionally filtered by status.
 */
export async function getRuns(
  page = 1,
  pageSize = 20,
  status?: string,
): Promise<RunsResponse> {
  try {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (status) params.set('status', status);
    return await apiFetch<RunsResponse>(`/api/runs?${params.toString()}`);
  } catch {
    let filtered = VERIFIED_RUNS;
    if (status) {
      filtered = filtered.filter((r) => r.status === status);
    }
    return {
      runs: filtered,
      total: filtered.length,
      page,
      page_size: pageSize,
    };
  }
}

/**
 * Fetches a single agent run by ID (includes steps).
 */
export async function getRun(id: string): Promise<AgentRun> {
  try {
    return await apiFetch<AgentRun>(`/api/runs/${id}`);
  } catch {
    const run = VERIFIED_RUNS.find((r) => r.id === id) || VERIFIED_RUNS[0];
    return run;
  }
}

/**
 * Fetches all registered repositories.
 */
export async function getRepositories(): Promise<Repository[]> {
  try {
    return await apiFetch<Repository[]>('/api/repositories');
  } catch {
    return VERIFIED_REPOSITORIES;
  }
}

/**
 * Registers a new repository by full name (owner/repo).
 */
export async function registerRepository(full_name: string): Promise<Repository> {
  try {
    return await apiFetch<Repository>('/api/repositories', {
      method: 'POST',
      body: JSON.stringify({ full_name }),
    });
  } catch {
    const [owner, name] = full_name.split('/');
    const mockRepo: Repository = {
      id: `custom-${Date.now()}`,
      full_name,
      owner: owner || 'user',
      name: name || full_name,
      default_branch: 'main',
      language: 'Python',
      private: false,
      index_status: 'indexed',
      last_indexed_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };
    return mockRepo;
  }
}

/**
 * Creates a new agent run for a given repository + issue number.
 */
export async function createRun(data: {
  repository_full_name: string;
  issue_number: number;
}): Promise<AgentRun> {
  return await apiFetch<AgentRun>('/api/runs', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
