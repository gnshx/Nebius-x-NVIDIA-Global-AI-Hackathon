<div align="center">

<img src="https://raw.githubusercontent.com/gnshx/Nebius-x-NVIDIA-Global-AI-Hackathon/main/assets/logo.png" alt="RepoMedic" width="120" />

# 🩺 RepoMedic

### Autonomous GitHub Issue-to-PR Agent

**Read a bug report. Understand the codebase. Write a fix. Verify it. Ship the PR.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-7C3AED?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

<br/>

[**Live Demo**](#running-the-demo) · [**Architecture**](#architecture) · [**Quick Start**](#quick-start) · [**API Docs**](#api-reference)

</div>

---

## Overview

RepoMedic is a production-grade autonomous agent that closes the loop between a GitHub issue and a verified pull request — without human intervention.

It does not suggest code. It **executes** code, observes test results, iterates on failures, and only opens a PR after sandbox verification succeeds.

```
/repomedic fix  ──→  [Nemotron reasons]  ──→  [Code modified]
                                                      │
                                              [Nebius Sandbox]
                                                      │
                                            ┌─────────┴─────────┐
                                       Tests pass?           Tests fail?
                                            │                    │
                                      [PR Created]      [Tavily Research]
                                                                 │
                                                        [Patch Revised]
                                                                 │
                                                        [Nebius Sandbox]
                                                                 │
                                                          Tests pass?
                                                                 │
                                                          [PR Created]
```

---

## Why RepoMedic

| Pain Point | RepoMedic's Answer |
|---|---|
| AI assistants suggest code but don't verify it | Every patch runs inside a real sandbox before a PR is opened |
| Autonomous agents loop forever | Hard iteration cap (`MAX_FIX_ITERATIONS=3`), enforced at the graph router |
| Generated patches can be malicious | `PatchValidator` blocks path traversal, `.git` manipulation, credential files |
| No audit trail | Every agent step is persisted to DB with input/output metadata |
| Context window overflow on large repos | pgvector semantic retrieval — only relevant code chunks are sent to the model |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                          GitHub App                                │
│              (webhook: issue_comment → /repomedic fix)             │
└─────────────────────────────┬──────────────────────────────────────┘
                              │  HMAC-verified webhook
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI  :8000                               │
│   POST /api/runs   GET /api/runs/{id}   GET /api/runs/{id}/events  │
│   POST /api/github/webhook    POST /api/repositories               │
└──────────────────┬───────────────────────────────────┬─────────────┘
                   │  Celery task                       │  SSE (Redis pub/sub)
                   ▼                                    ▼
┌──────────────────────────────┐         ┌─────────────────────────────┐
│      Celery Worker           │         │      Next.js  :3000         │
│  asyncio.run(graph.ainvoke)  │         │   Live run timeline         │
└──────────┬───────────────────┘         │   SSE → real-time updates   │
           │                             └─────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                           │
│                                                                      │
│  issue_analysis → repo_analysis → code_retrieval → planning         │
│       → implementation → test_generation → sandbox_execution        │
│           ↓ fail                  ↓ pass                            │
│  failure_analysis → web_research → patch_revision                   │
│  (loop max 3x)                                                       │
│           ↓ pass                                                     │
│       verification → pr_generation                                   │
└──────┬────────────────────┬───────────────────┬───────────────────┬─┘
       │                    │                   │                   │
       ▼                    ▼                   ▼                   ▼
 Nebius LLM API       Nebius Sandbox      PostgreSQL           GitHub REST
 (Nemotron)           (code execution)    + pgvector           API v4
                                          + Redis
                                                                    │
                                                             Tavily Search
                                                          (selective, audited)
```

### Agent State Machine

```
[issue_analysis]
      │
[repository_analysis]
      │
[code_retrieval]  ←── pgvector semantic search
      │
[planning]  ←── Nemotron Planner
      │
[implementation]  ←── Nemotron Coder + PatchValidator
      │
[test_generation]
      │
[sandbox_execution] ─── Nebius Sandbox
      │
      ├── PASS ──→ [verification] ──→ [pr_generation] ──→ GitHub PR ✅
      │
      └── FAIL ──→ [failure_analysis]
                        │
                        ├── requires_research=True ──→ [web_research] (Tavily)
                        │                                     │
                        └────────────────────────────→ [patch_revision]
                                                              │
                                                    [sandbox_execution]  (retry)
                                                              │
                                                    max 3 iterations
                                                              │
                                                     RUN_FAILED ❌ (no PR)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.12 + FastAPI | REST API, webhook receiver, SSE streaming |
| **Agent** | LangGraph | Explicit state-machine graph, no uncontrolled loops |
| **LLM** | NVIDIA Nemotron via Nebius | Planning, code generation, review |
| **Sandbox** | Nebius Token Factory | Isolated test execution (never on host) |
| **Code indexing** | tree-sitter + pgvector | Semantic retrieval — only relevant chunks sent to model |
| **Database** | PostgreSQL 16 + pgvector | Run state, code embeddings, audit trail |
| **Queue** | Redis + Celery | Background task execution, SSE pub/sub |
| **Frontend** | Next.js 14 + Tailwind + shadcn/ui | Live run dashboard |
| **GitHub** | GitHub App + REST API | Webhook trigger, branch/PR creation |
| **Search** | Tavily | Selective web research on unknown errors |
| **Observability** | structlog + OpenTelemetry | Structured, correlated logs |
| **Containers** | Docker + Compose | Reproducible local development |

---

## NVIDIA Nemotron Integration

Three configurable model slots — **zero hard-coded model names**:

```python
class ModelProvider:
    planner: ModelClient   # NEMOTRON_PLANNER_MODEL — planning, root-cause, review
    coder:   ModelClient   # NEMOTRON_CODER_MODEL   — code generation, patch revision
    fast:    ModelClient   # NEMOTRON_FAST_MODEL    — classification, ranking, summarization
```

Structured outputs via JSON schema injection — no regex parsing of model responses:

```python
issue_analysis = await model_provider.planner.generate_structured(
    messages, IssueAnalysis
)
# → Returns a validated IssueAnalysis Pydantic model
```

**Model routing:**

| Task | Model Slot |
|---|---|
| Root cause hypothesis | `planner` |
| Implementation plan | `planner` |
| Code + test generation | `coder` |
| Patch revision | `coder` |
| Failure classification | `fast` |
| File ranking, summarization | `fast` |
| Final patch review | `planner` |

---

## Nebius Token Factory Integration

Two distinct Nebius integrations:

### 1. LLM Inference
```python
client = ModelClient(model=settings.nemotron_planner_model)
response = await client.generate_structured(messages, ImplementationPlan)
```

### 2. Secure Sandbox Execution
```python
executor = SandboxExecutor()
sandbox_id = await executor.create_sandbox(repo_tarball)
await executor.apply_patch(sandbox_id, patch_content)
await executor.execute(sandbox_id, "pip install -e . -q")
result = await executor.execute(sandbox_id, "pytest --tb=short --json-report")
await executor.destroy(sandbox_id)  # always in finally block
```

**Execution guarantees:**
- Hard timeout per execution
- Max log size (50 KB stdout/stderr cap)
- Sandbox always destroyed in `finally` — no leaked resources
- Generated code never touches the API host filesystem

---

## Tavily Integration

Tavily is **not called on every failure** — only when the failure analysis determines external knowledge is needed:

```
ImportError: No module named 'xyz'
    → failure_category = DEPENDENCY_ERROR
    → requires_research = True
    → Tavily searches: '"xyz" library Python official documentation'
    → Results inform patch_revision
```

Every search is persisted with `query`, `reason`, `selected_sources`, and `timestamp` for full dashboard auditability.

---

## Security

| Concern | Mitigation |
|---|---|
| Malicious patches | `PatchValidator`: blocks `../`, `/` absolute paths, `.git/`, `.pem/.key/.env` |
| Credential exposure | Secret redaction before writing to `agent_steps.output_metadata` |
| Code execution on host | Never. All execution in Nebius Sandbox only |
| Infinite agent loops | Hard cap: `MAX_FIX_ITERATIONS=3`, enforced at graph router |
| Webhook spoofing | HMAC-SHA256 signature verified before any event processing |
| Duplicate PRs | Idempotency: rejects if PENDING/RUNNING run exists for same issue |
| GitHub permissions | Minimal: Issues (Read), Contents (Read+Write), Pull Requests (Read+Write) |

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- GitHub App credentials
- Nebius API key
- Tavily API key

### Setup

```bash
git clone https://github.com/gnshx/Nebius-x-NVIDIA-Global-AI-Hackathon
cd Nebius-x-NVIDIA-Global-AI-Hackathon/repomedic

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Build images, run migrations, start all services
make setup
make dev
```

| Service | URL |
|---|---|
| API + Swagger docs | http://localhost:8000/docs |
| Dashboard | http://localhost:3000 |
| Celery monitor | http://localhost:5555 |

---

## Running the Demo

The `demo/` directory contains a Python repository with an **intentional bug**:

```python
# demo/src/utils.py
def parse_user_id(value: str) -> int:
    parts = value.split(" ")  # ← BUG: should be split("-")
    return int(parts[1])      # IndexError on every call
```

**Demo test output (before fix):**
```
FAILED tests/test_utils.py::TestParseUserId::test_basic_parse    — IndexError
FAILED tests/test_utils.py::TestParseUserId::test_single_digit   — IndexError
FAILED tests/test_utils.py::TestParseUserId::test_large_id       — IndexError
FAILED tests/test_utils.py::TestParseUserId::test_roundtrip      — IndexError

4 failed, 12 passed in 0.02s
```

**To run end-to-end:**

1. Push `demo/` to a GitHub repository
2. Install the RepoMedic GitHub App on that repo
3. Create an issue using [`demo/ISSUE.md`](demo/ISSUE.md) as the template
4. Comment `/repomedic fix` on the issue
5. Watch the dashboard at `http://localhost:3000/runs`

**Or trigger via API:**
```bash
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"repository_full_name": "your/repo", "issue_number": 1}'
```

**Expected timeline (~90s):**
```
✅ Issue analyzed          — root cause: split(" ") should be split("-")
✅ Repository indexed      — 4 files, 16 functions
✅ Code retrieved          — src/utils.py, tests/test_utils.py
✅ Plan generated          — modify parse_user_id, update tests
✅ Patch generated         — unified diff, PatchValidator passed
✅ Sandbox run #1          — 4 failed (edge case missed)
🔎 Failure analyzed        — AssertionError → CODE_ERROR
✅ Patch revised
✅ Sandbox run #2          — 16 passed ✅
✅ Patch review approved
✅ PR created              → github.com/your/repo/pull/2
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/runs` | Trigger a new agent run |
| `GET` | `/api/runs` | List runs (paginated, filterable) |
| `GET` | `/api/runs/{id}` | Get run detail + all steps |
| `GET` | `/api/runs/{id}/events` | SSE stream for live updates |
| `POST` | `/api/runs/{id}/cancel` | Cancel a running agent |
| `POST` | `/api/repositories` | Register a repository |
| `GET` | `/api/repositories` | List registered repositories |
| `POST` | `/api/github/webhook` | GitHub App webhook receiver |
| `GET` | `/api/health` | Health check (DB + Redis) |

Full OpenAPI spec: `http://localhost:8000/docs`

---

## Project Structure

```
repomedic/
├── apps/
│   ├── api/
│   │   ├── agents/
│   │   │   ├── graph.py          # LangGraph state machine
│   │   │   ├── state.py          # RepoMedicState TypedDict
│   │   │   └── nodes/            # 12 node implementations
│   │   │       ├── base.py       # DB lifecycle + SSE helpers
│   │   │       ├── issue_analysis.py
│   │   │       ├── repository_analysis.py
│   │   │       ├── code_retrieval.py
│   │   │       ├── planning.py
│   │   │       ├── implementation.py
│   │   │       ├── test_generation.py
│   │   │       ├── sandbox_execution.py
│   │   │       ├── failure_analysis.py
│   │   │       ├── web_research.py
│   │   │       ├── patch_revision.py
│   │   │       ├── verification.py
│   │   │       └── pr_generation.py
│   │   ├── services/
│   │   │   ├── nebius/           # LLM client + sandbox executor
│   │   │   ├── github/           # App auth + REST client + webhook
│   │   │   ├── tavily/           # Selective web research
│   │   │   └── test_parser.py    # pytest JSON + text output parsing
│   │   ├── routes/               # FastAPI route handlers
│   │   ├── models/               # SQLAlchemy ORM + Pydantic schemas
│   │   ├── db/                   # Async engine + Alembic migrations
│   │   ├── celery_app.py         # Background task queue
│   │   └── config.py             # Pydantic settings
│   │
│   └── web/
│       ├── app/                  # Next.js 14 App Router pages
│       ├── components/           # RunTimeline, StepCard, badges
│       └── hooks/                # useRunEvents (SSE)
│
├── demo/                         # Reproducible demo repository
│   ├── src/utils.py              # Contains intentional bug
│   └── tests/test_utils.py      # 16 tests: 4 fail on bug
│
├── tests/
│   ├── unit/                     # Parser, validator, classifier tests
│   ├── integration/              # Webhook signature, API tests
│   └── e2e/                      # Full flow with mocked services
│
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://repomedic:repomedic@localhost:5432/repomedic
REDIS_URL=redis://localhost:6379/0

# GitHub App
GITHUB_APP_ID=
GITHUB_PRIVATE_KEY=                  # PEM key (or base64-encoded)
GITHUB_WEBHOOK_SECRET=

# Nebius Token Factory
NEBIUS_API_KEY=
NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1
NEBIUS_SANDBOX_URL=                  # Token Factory sandbox endpoint
NEBIUS_EMBEDDING_MODEL=BAAI/bge-en-icl

# NVIDIA Nemotron — never hard-coded
NEMOTRON_PLANNER_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
NEMOTRON_CODER_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
NEMOTRON_FAST_MODEL=nvidia/llama-3.1-nemotron-8b-instruct

# Tavily
TAVILY_API_KEY=

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Agent
MAX_FIX_ITERATIONS=3
APP_ENV=development
```

---

## Development Commands

```bash
make setup        # Install deps, build images, run migrations
make dev          # Start all services (API + Worker + Frontend + DB + Redis)
make test         # Run full test suite
make test-unit    # Unit tests only (no external services)
make lint         # ruff + mypy
make format       # ruff format
make migrate      # Run Alembic migrations
make demo         # Register demo repo + trigger agent run
make logs         # Follow API + worker logs
make clean        # Remove containers and volumes
```

---

## What's Implemented vs. Planned

### ✅ Implemented (MVP)
- Complete 12-node LangGraph state machine
- NVIDIA Nemotron model abstraction (3 configurable slots, structured outputs)
- Nebius Token Factory sandbox integration
- GitHub App authentication, webhook dispatch, PR creation
- tree-sitter parsing + pgvector semantic code retrieval
- pytest output parsing (JSON report + text fallback)
- Failure classification + selective Tavily research
- Final patch review gate (no PR without approval)
- Full REST API with SSE streaming
- Next.js dashboard with live run timeline
- Security: path validation, secret redaction, HMAC verification
- Demo repository with reproducible bug
- Unit + integration + e2e test suites

### 🔮 Roadmap
- Multi-language support (TypeScript, Go, Rust)
- GitHub Actions CI integration
- Slack / Discord notifications
- Advanced analytics dashboard
- Multi-repo batch processing
- PR auto-response to review comments
- Cost tracking per run

---

## Limitations

- **Python only**: Current MVP supports Python repositories with pytest. Other languages require adding language-specific sandbox commands.
- **Credentials**: Nebius Sandbox URL must be provided. Development mode falls back to Docker-based local execution.
- **Context window**: Very large repositories (>1M tokens) require tuning `MAX_CONTEXT_TOKENS`.

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Built for the **Nebius × NVIDIA Global AI Hackathon 2026**

**[github.com/gnshx/Nebius-x-NVIDIA-Global-AI-Hackathon](https://github.com/gnshx/Nebius-x-NVIDIA-Global-AI-Hackathon)**

</div>
