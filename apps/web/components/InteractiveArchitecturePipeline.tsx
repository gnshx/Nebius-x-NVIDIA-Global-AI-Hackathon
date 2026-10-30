'use client';

import React, { useState, useEffect } from 'react';
import { 
  GitPullRequest, 
  Cpu, 
  ShieldCheck, 
  Terminal, 
  Search, 
  Layers, 
  CheckCircle2, 
  ArrowRight, 
  Play, 
  RotateCcw, 
  Sparkles, 
  FileCode, 
  Check, 
  Copy,
  Activity,
  Zap,
  Lock
} from 'lucide-react';

interface StageData {
  id: string;
  number: string;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  color: string;
  badge: string;
  nodes: string[];
  telemetry: {
    engine: string;
    latency: string;
    throughput?: string;
    memory?: string;
    status: string;
  };
  inspector: {
    header: string;
    language: string;
    code: string;
    explanation: string;
  };
}

const STAGES: StageData[] = [
  {
    id: 'ingestion',
    number: '01',
    title: 'Webhook & Ingestion',
    subtitle: 'GitHub Issue Ingestion & Stacktrace Extraction',
    icon: GitPullRequest,
    color: 'from-blue-500/20 to-cyan-500/10 border-blue-500/40 text-blue-400',
    badge: 'LangGraph Webhook',
    nodes: ['GitHub Webhook Listener', 'Issue #466 Parser', 'Reproduction Constraint Extractor'],
    telemetry: {
      engine: 'FastAPI Webhook + LangGraph v0.2',
      latency: '180ms',
      throughput: '12 req/sec',
      memory: '48 MB',
      status: 'VERIFIED',
    },
    inspector: {
      header: 'GitHub Issue #466 Ingestion Payload',
      language: 'json',
      code: `{
  "repository": "python-humanize/humanize",
  "issue_number": 466,
  "title": "intcomma() with negative ndigits raises ValueError",
  "error_type": "ValueError: Format specifier missing precision",
  "call_stack": [
    "humanize/number.py:58 in intcomma",
    "format(value, f'.{ndigits}f')"
  ],
  "reproduction": "intcomma(1234.56, ndigits=-1)",
  "security_gate": "whitelisted_repo_only"
}`,
      explanation: 'Extracts reproduction constraints and isolates targeted function calls directly from GitHub markdown issue threads.',
    },
  },
  {
    id: 'ast',
    number: '02',
    title: 'Tree-sitter AST Slicing',
    subtitle: 'Zero-Hallucination Symbol Call Graph Indexing',
    icon: FileCode,
    color: 'from-purple-500/20 to-pink-500/10 border-purple-500/40 text-purple-400',
    badge: 'Language-Aware Parser',
    nodes: ['Tree-sitter AST Parser', 'Call Hierarchy Traversal', 'Context Window Optimizer (1,420 tok)'],
    telemetry: {
      engine: 'Tree-sitter Python Grammar v0.21',
      latency: '240ms',
      throughput: '4,500 AST nodes/s',
      memory: '64 MB',
      status: 'INDEXED',
    },
    inspector: {
      header: 'Tree-sitter S-Expression AST Chunk',
      language: 'python',
      code: `(function_definition
  name: (identifier) @func.name (#eq? @func.name "intcomma")
  parameters: (parameters
    (identifier) @param.value
    (default_parameter (identifier) @param.ndigits (integer)))
  body: (block
    (comment) @docstring
    ;; Extracted targeted slice (lines 50-74)
    ;; 0 irrelevant repo files sent to LLM context
    (return_statement)))`,
      explanation: 'Language-aware grammar parsing extracts exact function slices and variable scopes, eliminating token bloat and hallucination.',
    },
  },
  {
    id: 'ai_engine',
    number: '03',
    title: 'Nemotron 30B MoE Engine',
    subtitle: 'NVIDIA NIM API with Streaming CoT Reasoning',
    icon: Cpu,
    color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/40 text-emerald-400',
    badge: 'NVIDIA Nemotron 3.5',
    nodes: ['NVIDIA Nemotron 3.5 Lightning (30B A3B)', 'Streaming Chain-of-Thought (<thought>)', 'Tavily API Drift Intelligence'],
    telemetry: {
      engine: 'NVIDIA NIM API (Nemotron 30B MoE Cluster)',
      latency: '28ms / token',
      throughput: '38.4 tok/sec',
      memory: '30B MoE (3.5B active)',
      status: '3,420 CoT TOKENS',
    },
    inspector: {
      header: 'Nemotron 30B Chain-of-Thought Reasoning Stream',
      language: 'markdown',
      code: `<thought>
1. Issue analysis: intcomma() crashes when ndigits is negative (-1).
2. Root cause: f".{ndigits}f" evaluates to f".-1f", invalid Python float format specifier.
3. Decision: Explicit input validation at entry point of intcomma().
4. Validation rule: if ndigits < 0: raise ValueError("ndigits must be non-negative").
5. Regression test: Create test_intcomma_negative_ndigits() asserting ValueError.
6. Target file: src/humanize/number.py (lines 58-62).
</thought>`,
      explanation: '30B Mixture-of-Experts model activates ~3.5B parameters per token, delivering sub-second deep chain-of-thought code reasoning.',
    },
  },
  {
    id: 'sandbox',
    number: '04',
    title: 'Deterministic Sandbox',
    subtitle: 'Isolated Docker Container with Full Pytest Verification',
    icon: Terminal,
    color: 'from-amber-500/20 to-orange-500/10 border-amber-500/40 text-amber-400',
    badge: 'Zero-Hallucination Gate',
    nodes: ['Isolated Pytest Container', 'Self-Healing 3-Iteration Cycle', '241/241 Tests Passing (0.20s)'],
    telemetry: {
      engine: 'Isolated Docker / Local Execution Sandbox',
      latency: '0.20s pytest runtime',
      throughput: '241/241 tests passing',
      memory: '142 MB container limit',
      status: 'ZERO REGRESSIONS',
    },
    inspector: {
      header: 'Sandbox Test Execution Stream (pytest)',
      language: 'bash',
      code: `============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-8.1.1, pluggy-1.4.0
rootdir: /sandbox/workspace/humanize
collected 241 items

tests/test_number.py::test_intcomma PASSED                               [ 42%]
tests/test_number.py::test_intcomma_negative_ndigits PASSED              [ 43%]
tests/test_number.py::test_fractional PASSED                             [ 44%]
...
======================== 241 passed in 0.20s ===========================`,
      explanation: 'Strict pass/fail gate. Pull requests are strictly blocked at the deterministic verification gate unless all sandbox unit tests pass.',
    },
  },
  {
    id: 'dispatch',
    number: '05',
    title: 'Security Gate & PR Dispatch',
    subtitle: 'PatchValidator AST Guard & Signed GitHub PR Creation',
    icon: ShieldCheck,
    color: 'from-emerald-500/25 to-green-500/10 border-emerald-500/50 text-emerald-400',
    badge: 'Production PR Created',
    nodes: ['PatchValidator AST Security Guard', 'Verification Auditor (correct=True)', 'GitHub PR #467 Created & Dispatched'],
    telemetry: {
      engine: 'PatchValidator AST Guard + GitHub REST API',
      latency: '320ms',
      throughput: '1 PR / run',
      memory: '32 MB',
      status: 'PR #467 OPEN',
    },
    inspector: {
      header: 'Automated Pull Request Dispatch & Metadata',
      language: 'markdown',
      code: `## Summary of Fix
- Added input validation in \`src/humanize/number.py\`:
  \`\`\`python
  if ndigits < 0:
      raise ValueError("ndigits must be non-negative")
  \`\`\`
- Added targeted regression test in \`tests/test_number.py\`.
- Sandbox Verification: 241/241 passed (0 regressions).
- Target PR: https://github.com/python-humanize/humanize/pull/467`,
      explanation: 'Hardened AST guard enforces zero path traversals, whitelisted diff boundaries, and verifiable test proof before opening PR.',
    },
  },
];

export function InteractiveArchitecturePipeline() {
  const [activeStageId, setActiveStageId] = useState<string>('ai_engine');
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const activeStage = STAGES.find((s) => s.id === activeStageId) || STAGES[2];

  // Automated Sequential Pipeline Simulation
  useEffect(() => {
    if (!isSimulating) return;

    const stageIds = STAGES.map((s) => s.id);
    let currentIndex = 0;

    const interval = setInterval(() => {
      currentIndex += 1;
      if (currentIndex >= stageIds.length) {
        setIsSimulating(false);
        clearInterval(interval);
      } else {
        setActiveStageId(stageIds[currentIndex]);
      }
    }, 1800);

    return () => clearInterval(interval);
  }, [isSimulating]);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(activeStage.inspector.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleStartSimulation = () => {
    setActiveStageId(STAGES[0].id);
    setIsSimulating(true);
  };

  return (
    <div className="rounded-2xl border border-border/80 bg-gradient-to-b from-card/95 via-card/70 to-card/90 shadow-2xl overflow-hidden backdrop-blur-xl">
      {/* Top Interactive Control Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 sm:px-6 border-b border-border/60 bg-muted/20">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground font-semibold">
              Interactive 5-Stage Agentic Pipeline
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Live Flow Architecture
            </span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold tracking-tight mt-1 text-foreground">
            End-to-End Autonomous Issue-to-PR Execution Pipeline
          </h3>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleStartSimulation}
            disabled={isSimulating}
            className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold shadow-sm transition-all ${
              isSimulating
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 cursor-wait'
                : 'bg-primary text-primary-foreground hover:opacity-90 active:scale-95'
            }`}
          >
            {isSimulating ? (
              <>
                <RotateCcw className="h-3.5 w-3.5 animate-spin" />
                <span>Simulating Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Simulate Agent Flow</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Stage Flow Strip */}
      <div className="p-4 sm:p-6 bg-tech-grid relative">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {STAGES.map((stage, idx) => {
            const Icon = stage.icon;
            const isActive = stage.id === activeStageId;

            return (
              <div
                key={stage.id}
                onClick={() => {
                  setIsSimulating(false);
                  setActiveStageId(stage.id);
                }}
                className={`relative rounded-xl border p-4 cursor-pointer transition-all duration-200 select-none ${
                  isActive
                    ? 'border-emerald-500/60 bg-gradient-to-br from-emerald-500/10 via-zinc-900/90 to-card shadow-lg ring-1 ring-emerald-500/30 -translate-y-0.5'
                    : 'border-border/60 bg-card/60 hover:bg-muted/40 hover:border-border'
                }`}
              >
                {/* Stage Index & Badge */}
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[11px] font-mono font-bold ${isActive ? 'text-emerald-400' : 'text-muted-foreground'}`}>
                    STAGE {stage.number}
                  </span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                        : 'bg-muted text-muted-foreground border-transparent'
                    }`}
                  >
                    {stage.badge}
                  </span>
                </div>

                {/* Stage Title & Icon */}
                <div className="flex items-start gap-2.5 mb-2">
                  <div
                    className={`p-2 rounded-lg shrink-0 ${
                      isActive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-muted/80 text-muted-foreground'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-xs sm:text-sm text-foreground leading-snug">
                      {stage.title}
                    </h4>
                    <p className="text-[11px] text-muted-foreground line-clamp-1 mt-0.5">
                      {stage.subtitle}
                    </p>
                  </div>
                </div>

                {/* Micro Node Badges */}
                <div className="space-y-1 pt-1 border-t border-border/40">
                  {stage.nodes.slice(0, 2).map((node, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-[10px] text-muted-foreground truncate">
                      <span className={`h-1 w-1 rounded-full ${isActive ? 'bg-emerald-400' : 'bg-muted-foreground/40'}`} />
                      <span className="truncate">{node}</span>
                    </div>
                  ))}
                </div>

                {/* Active Indicator Underline */}
                {isActive && (
                  <div className="absolute -bottom-[1px] left-4 right-4 h-[2px] bg-gradient-to-r from-emerald-500 via-cyan-400 to-purple-500 rounded-full" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Stage Telemetry & Data Inspector */}
      <div className="border-t border-border/80 bg-zinc-950/90 p-5 sm:p-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Telemetry & Stage Summary (4 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono font-bold text-emerald-400 uppercase">
                  Stage {activeStage.number} Execution Telemetry
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {activeStage.telemetry.status}
                </span>
              </div>
              <h4 className="text-lg font-bold text-foreground">
                {activeStage.title}
              </h4>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                {activeStage.inspector.explanation}
              </p>
            </div>

            {/* Telemetry Metrics Grid */}
            <div className="grid grid-cols-2 gap-2.5 text-xs">
              <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
                <span className="text-[10px] uppercase font-mono text-muted-foreground block mb-1">
                  Engine / Architecture
                </span>
                <span className="font-semibold text-foreground text-xs block truncate">
                  {activeStage.telemetry.engine}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
                <span className="text-[10px] uppercase font-mono text-muted-foreground block mb-1">
                  Execution Latency
                </span>
                <span className="font-mono font-bold text-emerald-400 text-xs block">
                  {activeStage.telemetry.latency}
                </span>
              </div>
              {activeStage.telemetry.throughput && (
                <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
                  <span className="text-[10px] uppercase font-mono text-muted-foreground block mb-1">
                    Throughput Rate
                  </span>
                  <span className="font-mono text-foreground text-xs block">
                    {activeStage.telemetry.throughput}
                  </span>
                </div>
              )}
              {activeStage.telemetry.memory && (
                <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800">
                  <span className="text-[10px] uppercase font-mono text-muted-foreground block mb-1">
                    Resource Footprint
                  </span>
                  <span className="font-mono text-foreground text-xs block">
                    {activeStage.telemetry.memory}
                  </span>
                </div>
              )}
            </div>

            {/* Nodes Involved Checklist */}
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/80 space-y-2">
              <span className="text-[11px] font-mono font-semibold text-muted-foreground block">
                State Machine Node Graph:
              </span>
              <div className="space-y-1.5">
                {activeStage.nodes.map((node, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-zinc-300">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    <span>{node}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Code & Payload Inspector (7 cols) */}
          <div className="lg:col-span-7 flex flex-col justify-between">
            <div className="rounded-xl border border-zinc-800 bg-black/80 overflow-hidden shadow-inner flex flex-col h-full">
              {/* Inspector Header */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-900/60">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                  </div>
                  <span className="font-mono text-[11px] text-zinc-400 pl-2">
                    {activeStage.inspector.header}
                  </span>
                </div>
                <button
                  onClick={handleCopyCode}
                  className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-zinc-200 transition-colors px-2 py-0.5 rounded hover:bg-zinc-800"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Code Payload Content */}
              <div className="p-4 overflow-x-auto font-mono text-xs text-zinc-300 leading-relaxed max-h-80 select-text bg-black/60">
                <pre>
                  <code>{activeStage.inspector.code}</code>
                </pre>
              </div>

              {/* Footer Note */}
              <div className="px-4 py-2 border-t border-zinc-800/80 bg-zinc-900/30 text-[11px] text-zinc-500 flex items-center justify-between">
                <span>Deterministic Zero-Hallucination Pipeline</span>
                <span className="font-mono text-emerald-400/80">LangGraph Cyclic Graph</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
