export type RunStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED' | 'TIMED_OUT';
export type StepStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'SKIPPED';
export type StepType =
  | 'issue_analysis'
  | 'repository_analysis'
  | 'code_retrieval'
  | 'planning'
  | 'implementation'
  | 'test_generation'
  | 'sandbox_execution'
  | 'failure_analysis'
  | 'web_research'
  | 'patch_revision'
  | 'verification'
  | 'pr_generation';

export interface AgentStep {
  id: string;
  run_id: string;
  step_type: StepType;
  status: StepStatus;
  iteration: number;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  model_used: string | null;
  input_metadata: Record<string, unknown>;
  output_metadata: Record<string, unknown>;
  error: string | null;
  created_at: string;
}

export interface AgentRun {
  id: string;
  repository_id: string;
  issue_number: number;
  status: RunStatus;
  iteration: number;
  max_iterations: number;
  triggered_by: string;
  started_at: string | null;
  completed_at: string | null;
  pr_url: string | null;
  pr_number: number | null;
  branch_name: string | null;
  error: string | null;
  steps: AgentStep[];
  created_at: string;
}

export interface Repository {
  id: string;
  full_name: string;
  owner: string;
  name: string;
  default_branch: string;
  language: string | null;
  private: boolean;
  index_status: string;
  last_indexed_at: string | null;
  created_at: string;
}

export interface RunsResponse {
  runs: AgentRun[];
  total: number;
  page: number;
  page_size: number;
}
