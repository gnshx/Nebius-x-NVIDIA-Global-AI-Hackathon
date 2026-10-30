import Link from 'next/link';
import { getRuns } from '@/lib/api';
import { RunStatusBadge } from '@/components/RunStatusBadge';
import { truncateId, formatDate } from '@/lib/utils';
import { 
  Activity, 
  CheckCircle2, 
  GitPullRequest, 
  Zap, 
  ArrowRight, 
  Cpu, 
  ShieldCheck, 
  Search, 
  Terminal, 
  Layers, 
  Sparkles,
  ExternalLink,
  Code2,
  Box,
  Compass
} from 'lucide-react';
import { AgentRun } from '@/lib/types';
import { ThreeAgentVisualizer } from '@/components/ThreeAgentVisualizer';
import { InteractiveArchitecturePipeline } from '@/components/InteractiveArchitecturePipeline';
import { InteractiveWorkbenchPreview } from '@/components/InteractiveWorkbenchPreview';
import { RepoMedicLogo } from '@/components/RepoMedicLogo';

async function getStats() {
  try {
    const allRuns = await getRuns(1, 100);
    const runs = allRuns.runs ?? [];
    return { recent: runs.slice(0, 5) };
  } catch {
    return { recent: [] };
  }
}

export default async function HomePage() {
  const { recent } = await getStats();

  return (
    <div className="space-y-16 pb-16">
      {/* Track & Model Header Badges */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm">
          <Sparkles className="h-3.5 w-3.5" />
          Nebius × NVIDIA Global AI Hackathon
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-sm">
          <Layers className="h-3.5 w-3.5" />
          Coding & Agentic Engineering Track
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 shadow-sm">
          <Cpu className="h-3.5 w-3.5" />
          Nemotron 3.5 Lightning (30B MoE)
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm">
          <Search className="h-3.5 w-3.5" />
          Tavily API Drift Intelligence
        </span>
      </div>

      {/* Hero Section */}
      <section className="text-center space-y-6 max-w-4xl mx-auto">
        <div className="flex justify-center">
          <RepoMedicLogo size="lg" className="animate-pulse-glow" />
        </div>
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-zinc-100 via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
          RepoMedic
        </h1>
        <p className="text-xl sm:text-2xl font-semibold text-foreground">
          Autonomous GitHub Issue-to-PR Verification Agent
        </p>
        <p className="text-base sm:text-lg text-muted-foreground leading-relaxed max-w-3xl mx-auto">
          Powered by <strong className="text-foreground">NVIDIA Nemotron 3.5 Lightning (30B MoE)</strong> via <strong className="text-foreground">NVIDIA NIM API</strong>. Diagnoses issues, semantically retrieves code with Tree-sitter AST parsing, validates security constraints, and executes unit tests inside an isolated sandbox before opening <span className="text-emerald-400 font-semibold">100% test-verified pull requests</span>.
        </p>

        {/* Primary Action Buttons */}
        <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/runs"
            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 px-6 py-3 rounded-lg font-semibold transition-all text-sm shadow-lg shadow-emerald-500/20 active:scale-95"
          >
            Launch Live Dashboard <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#threejs-canvas"
            className="inline-flex items-center gap-2 border border-zinc-800 bg-card/80 backdrop-blur-sm px-5 py-3 rounded-lg font-medium hover:bg-muted/50 hover:border-zinc-700 transition-all text-sm"
          >
            <Box className="h-4 w-4 text-emerald-400" />
            Interactive 3D Agent Canvas
          </a>
          <a
            href="#architecture-pipeline"
            className="inline-flex items-center gap-2 border border-zinc-800 bg-card/80 backdrop-blur-sm px-5 py-3 rounded-lg font-medium hover:bg-muted/50 hover:border-zinc-700 transition-all text-sm"
          >
            <Layers className="h-4 w-4 text-cyan-400" />
            Interactive Pipeline Flow
          </a>
          <a
            href="#developer-workbench"
            className="inline-flex items-center gap-2 border border-zinc-800 bg-card/80 backdrop-blur-sm px-5 py-3 rounded-lg font-medium hover:bg-muted/50 hover:border-zinc-700 transition-all text-sm"
          >
            <Terminal className="h-4 w-4 text-purple-400" />
            Live Workbench
          </a>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border bg-card p-5 space-y-2 shadow-sm hover:border-emerald-500/40 transition-colors">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 w-fit">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-sm">Zero Hallucination Gate</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Strict pass/fail gate. Pull requests are never dispatched unless 100% of sandbox pytest tests pass.
          </p>
        </div>

        <div className="rounded-xl border bg-card p-5 space-y-2 shadow-sm hover:border-purple-500/40 transition-colors">
          <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400 w-fit">
            <Cpu className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-sm">Nemotron 30B MoE</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            30B parameter Mixture-of-Experts activating ~3.5B params per token with sub-second chain-of-thought.
          </p>
        </div>

        <div className="rounded-xl border bg-card p-5 space-y-2 shadow-sm hover:border-blue-500/40 transition-colors">
          <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400 w-fit">
            <Code2 className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-sm">Tree-sitter AST Slicing</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Language-aware AST parsing indexes symbols, definitions, and callers without sending entire repos to LLM.
          </p>
        </div>

        <div className="rounded-xl border bg-card p-5 space-y-2 shadow-sm hover:border-amber-500/40 transition-colors">
          <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 w-fit">
            <Search className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-sm">Tavily Deep Research</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Selectively queries live documentation, GitHub issues, and PEP standards when API drift is detected.
          </p>
        </div>
      </section>

      {/* 3D Three.js Interactive Agent Visualizer (Replacing Plain Video) */}
      <section id="threejs-canvas" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
              <Box className="h-3.5 w-3.5" />
              Interactive Three.js 3D Architecture Canvas
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Autonomous 12-Node Agent State Machine
            </h2>
            <p className="text-sm text-muted-foreground">
              Interact with RepoMedic&apos;s 3D state machine. Drag to orbit, click any node to inspect live telemetry, and sync audio narration.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-zinc-400 bg-muted px-2.5 py-1 rounded border">
              WebGL 60 FPS • 100% Local TTS
            </span>
          </div>
        </div>

        {/* Three.js Canvas Component */}
        <ThreeAgentVisualizer />
      </section>

      {/* Real-World Open-Source Verification Proof Showcase */}
      <section id="opensource-proof" className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Verified Production Proof
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Open-Source Bug Fix: <span className="text-primary font-mono text-xl sm:text-2xl">python-humanize/humanize</span> #466
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Live authentic bug resolution in a 2,500+ star open-source repository verified in an isolated execution sandbox.
            </p>
          </div>
          <a
            href="https://github.com/python-humanize/humanize/pull/467"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 border border-emerald-500/30 bg-emerald-500/5 px-3.5 py-2 rounded-lg hover:bg-emerald-500/10 transition-colors shrink-0"
          >
            Inspect GitHub PR #467 <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Proof Summary Card */}
          <div className="rounded-xl border bg-card p-6 space-y-4 shadow-sm lg:col-span-2">
            <h3 className="font-semibold text-lg flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
              12-Node Pipeline Execution Summary
            </h3>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <a 
                href="https://github.com/python-humanize/humanize"
                target="_blank"
                rel="noopener noreferrer"
                className="p-3 rounded-lg bg-muted/40 border hover:border-primary/50 transition-colors block group"
              >
                <span className="text-xs text-muted-foreground block">Target Repo</span>
                <span className="font-mono text-xs font-bold truncate block group-hover:text-primary flex items-center justify-center gap-1">
                  humanize (2.5k★) <ExternalLink className="h-3 w-3 opacity-60" />
                </span>
              </a>
              <a 
                href="https://github.com/python-humanize/humanize/issues/466"
                target="_blank"
                rel="noopener noreferrer"
                className="p-3 rounded-lg bg-muted/40 border hover:border-amber-500/50 transition-colors block group"
              >
                <span className="text-xs text-muted-foreground block">Target Issue</span>
                <span className="font-mono text-xs font-bold text-amber-400 block group-hover:underline flex items-center justify-center gap-1">
                  Issue #466 <ExternalLink className="h-3 w-3 opacity-60" />
                </span>
              </a>
              <div className="p-3 rounded-lg bg-muted/40 border">
                <span className="text-xs text-muted-foreground block">Sandbox Tests</span>
                <span className="font-mono text-xs font-bold text-emerald-400 block">241/241 Passed</span>
              </div>
              <div className="p-3 rounded-lg bg-muted/40 border">
                <span className="text-xs text-muted-foreground block">Model Engine</span>
                <span className="font-mono text-xs font-bold text-purple-400 block">Nemotron 30B MoE</span>
              </div>
            </div>

            <div className="space-y-2 text-sm text-muted-foreground pt-1">
              <p>
                <strong className="text-foreground">Reported Bug:</strong> Passing negative <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">ndigits=-1</code> to <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">intcomma()</code> crashed with an obscure <code className="text-xs text-red-400 font-mono">ValueError: Format specifier missing precision</code>.
              </p>
              <p>
                <strong className="text-foreground">Nemotron 30B MoE Diagnosis:</strong> Located <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">src/humanize/number.py</code>, synthesized input validation <code className="text-xs text-emerald-400 font-mono">if ndigits &lt; 0: raise ValueError(&quot;ndigits must be non-negative&quot;)</code>, added targeted regression tests in <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">tests/test_number.py</code>, and ran full pytest in the isolated sandbox with <span className="text-emerald-400 font-semibold">241 tests passing (0 failures, 0 regressions)</span>.
              </p>
            </div>

            {/* Local Reproduction Command */}
            <div className="pt-2">
              <span className="text-xs font-semibold text-muted-foreground block mb-1.5">
                Run this open-source proof locally:
              </span>
              <div className="flex items-center justify-between bg-muted/70 border rounded-lg px-3 py-2 font-mono text-xs overflow-x-auto">
                <code>python3 scripts/run_opensource_proof.py</code>
                <span className="text-[11px] text-muted-foreground shrink-0 ml-2">~210s end-to-end</span>
              </div>
            </div>
          </div>

          {/* Quick Telemetry Box */}
          <div className="rounded-xl border bg-card p-6 space-y-4 shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="font-semibold text-base mb-3 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" />
                Proof Execution Telemetry
              </h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between pb-2 border-b">
                  <span className="text-muted-foreground">State Machine Stages</span>
                  <span className="font-mono font-bold">12 / 12 Nodes Passed</span>
                </div>
                <div className="flex justify-between pb-2 border-b">
                  <span className="text-muted-foreground">Sandbox Test Suite</span>
                  <span className="font-mono font-bold text-emerald-400">241 Passed (0.20s)</span>
                </div>
                <div className="flex justify-between pb-2 border-b">
                  <span className="text-muted-foreground">Security Gate</span>
                  <span className="font-mono font-bold text-emerald-400">PatchValidator PASSED</span>
                </div>
                <div className="flex justify-between pb-2 border-b">
                  <span className="text-muted-foreground">Verification Auditor</span>
                  <span className="font-mono font-bold text-emerald-400">APPROVED (correct=True)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Target Branch</span>
                  <span className="font-mono">repomedic/fix/issue-466</span>
                </div>
              </div>
            </div>

            <Link
              href="/runs/55f677a5-01af-4011-857a-bbc83740a908"
              className="w-full text-center py-2.5 px-4 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-1.5 shadow-sm"
            >
              <span>View Full 12-Step In-App Trace</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Core Hackathon Innovations (No Scores/Percentages, Pure Technological Excellence) */}
      <section className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Key Architectural Innovations
          </h2>
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            Architected specifically for the Nebius × NVIDIA Global AI Hackathon (Coding & Agentic Engineering Track).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Pillar 1: Technological Implementation */}
          <div className="rounded-xl border bg-card p-6 space-y-3 shadow-sm hover:border-primary/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-base">NVIDIA Nemotron 30B MoE Engine</h3>
                <span className="text-xs text-muted-foreground">Sub-second Latency & Active Chain-of-Thought</span>
              </div>
            </div>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
              <li>
                <strong className="text-foreground">Nemotron 3.5 Lightning (30B A3B):</strong> 30 billion total parameters with ~3.5 billion active per token served via NVIDIA NIM with streaming chain-of-thought tokens (<code className="text-xs bg-muted px-1 py-0.5 rounded font-mono">enable_thinking=True</code>).
              </li>
              <li>
                <strong className="text-foreground">12-Node Cyclic LangGraph:</strong> Full state machine with triager, planner, coder, test synthesizer, reflection, and gate nodes.
              </li>
              <li>
                <strong className="text-foreground">Tree-sitter AST Analysis:</strong> Language-aware code chunking indexing symbols and cross-file dependencies.
              </li>
              <li>
                <strong className="text-foreground">PatchValidator Security Guard:</strong> Hardened security layer blocking absolute paths, directory traversals, and non-whitelisted files.
              </li>
            </ul>
          </div>

          {/* Pillar 2: Zero-Hallucination Guarantee */}
          <div className="rounded-xl border bg-card p-6 space-y-3 shadow-sm hover:border-primary/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-base">The Zero-Hallucination Guarantee</h3>
                <span className="text-xs text-muted-foreground">Deterministic Sandbox Verification Gate</span>
              </div>
            </div>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
              <li>
                <strong className="text-foreground">Zero Hallucinated PRs:</strong> Most coding assistants create unverified diffs that break CI. RepoMedic executes tests inside a sandbox and strictly rejects PR creation unless 100% of tests pass.
              </li>
              <li>
                <strong className="text-foreground">Self-Healing 3-Iteration Cycle:</strong> If tests fail, the agent parses the pytest stack trace, reflects on the failure mode, and re-plans repairs automatically.
              </li>
              <li>
                <strong className="text-foreground">Regression Test Synthesis:</strong> Synthesizes new targeted regression test cases before modifying production code.
              </li>
            </ul>
          </div>

          {/* Pillar 3: Real-time Developer Observability */}
          <div className="rounded-xl border bg-card p-6 space-y-3 shadow-sm hover:border-primary/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400">
                <Code2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-base">Real-time Developer Observability</h3>
                <span className="text-xs text-muted-foreground">Full Telemetry Across All 12 Nodes</span>
              </div>
            </div>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
              <li>
                <strong className="text-foreground">Live Node Stepper:</strong> Step-by-step visual tracker showing real-time agent progression across all 12 nodes.
              </li>
              <li>
                <strong className="text-foreground">Unified Diff Viewer:</strong> Clear color-coded file diffs highlighting additions, deletions, and AST modifications.
              </li>
              <li>
                <strong className="text-foreground">Terminal Test Execution Logs:</strong> Real-time streaming of sandbox pytest output, showing exact pass/fail counters.
              </li>
              <li>
                <strong className="text-foreground">Automated PR Documentation:</strong> Formats clean PR markdown with reproduction steps, fix explanations, and test evidence.
              </li>
            </ul>
          </div>

          {/* Pillar 4: Eliminating Maintainer Burnout */}
          <div className="rounded-xl border bg-card p-6 space-y-3 shadow-sm hover:border-primary/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400">
                <GitPullRequest className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-base">Eliminating Maintainer Burnout</h3>
                <span className="text-xs text-muted-foreground">Hours of Triage Reduced to Minutes of Automated Execution</span>
              </div>
            </div>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
              <li>
                <strong className="text-foreground">Velocity Shift:</strong> Open-source maintainers spend 40% of their time triaging issues and reviewing broken PRs. RepoMedic reduces resolution time from hours of manual triage down to 1-3 minutes of automated, test-verified execution.
              </li>
              <li>
                <strong className="text-foreground">High-Confidence Automation:</strong> By enforcing strict sandbox verification, maintainers can safely enable automated merge for verified low-risk bug fixes.
              </li>
              <li>
                <strong className="text-foreground">Drop-In GitHub App:</strong> Installs on any repository with zero configuration changes required.
              </li>
            </ul>
          </div>
        </div>

        {/* Sponsor Highlight: Tavily Deep Research */}
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400">
              <Search className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-base text-amber-400">Autonomous Knowledge Engine: Tavily Deep API Research</h3>
              <span className="text-xs text-muted-foreground">Real-time External Documentation & API Drift Intelligence</span>
            </div>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            When bug reports involve third-party dependency updates or breaking API changes (e.g., deprecated function arguments or framework migrations), RepoMedic automatically invokes <strong className="text-foreground">Tavily AI Search</strong> to fetch real-time documentation, changelogs, and GitHub migration discussions before drafting the code repair.
          </p>
        </div>
      </section>

      {/* Interactive System Architecture Pipeline Component */}
      <section id="architecture-pipeline" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
              <Layers className="h-3.5 w-3.5" />
              Live Interactive Architecture
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Interactive 5-Stage System Pipeline
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Click through the stages or simulate live execution to inspect AST trees, chain-of-thought tokens, and sandbox verification.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded">
              12 Nodes Active • LangGraph Cyclic
            </span>
          </div>
        </div>
        
        <InteractiveArchitecturePipeline />
      </section>

      {/* Interactive Developer Workbench & Execution Environment */}
      <section id="developer-workbench" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-2">
              <Terminal className="h-3.5 w-3.5" />
              Interactive Developer Workbench
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Live Verification Workbench & Diff Viewer
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Switch between the unified syntax-highlighted diff, interactive pytest sandbox runner, and Nemotron 30B reasoning inspector.
            </p>
          </div>
          <Link 
            href="/runs/55f677a5-01af-4011-857a-bbc83740a908" 
            className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg hover:bg-emerald-500/20 transition-colors shrink-0"
          >
            <span>Open Full Telemetry Page</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
        
        <InteractiveWorkbenchPreview />
      </section>

      {/* Live Agent Execution History */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Live Agent Execution History</h2>
          <Link href="/runs" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
            View All Runs <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {recent.length === 0 ? (
          <div className="rounded-xl border bg-card p-8 text-center text-muted-foreground">
            <Activity className="h-8 w-8 mx-auto mb-3 opacity-40" />
            <p>No runs registered in database yet. Launch the live demo script to see a live execution run.</p>
            <div className="mt-4">
              <code className="text-xs bg-muted px-3 py-1.5 rounded font-mono">
                python3 scripts/run_live_demo.py
              </code>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
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
    </div>
  );
}
