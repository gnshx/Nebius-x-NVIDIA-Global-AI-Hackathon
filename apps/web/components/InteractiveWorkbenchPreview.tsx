'use client';

import React, { useState } from 'react';
import { 
  Terminal, 
  Code2, 
  CheckCircle2, 
  Cpu, 
  GitBranch, 
  FileCode, 
  Play, 
  RotateCcw, 
  ShieldCheck, 
  ExternalLink,
  Layers,
  ChevronRight,
  Sparkles
} from 'lucide-react';

export function InteractiveWorkbenchPreview() {
  const [activeTab, setActiveTab] = useState<'diff' | 'pytest' | 'cot' | 'ast'>('diff');
  const [isTestRunning, setIsTestRunning] = useState<boolean>(false);
  const [testRunCount, setTestRunCount] = useState<number>(241);

  const handleRerunPytest = () => {
    setIsTestRunning(true);
    setTimeout(() => {
      setIsTestRunning(false);
      setTestRunCount(241);
    }, 1200);
  };

  return (
    <div className="rounded-2xl border border-zinc-800 bg-[#0c1017] shadow-2xl overflow-hidden font-sans">
      {/* IDE Window Title Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#161b22] border-b border-zinc-800 select-none">
        <div className="flex items-center gap-3">
          {/* macOS Window Controls */}
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#ff5f56] border border-[#e0443e]" />
            <div className="w-3 h-3 rounded-full bg-[#ffbd2e] border border-[#dea123]" />
            <div className="w-3 h-3 rounded-full bg-[#27c93f] border border-[#1aab29]" />
          </div>

          <div className="h-4 w-[1px] bg-zinc-700/60 mx-1 hidden sm:block" />

          {/* Repo & Branch Pill */}
          <div className="flex items-center gap-2 text-xs text-zinc-300">
            <span className="font-semibold text-zinc-200">python-humanize/humanize</span>
            <span className="text-zinc-500">/</span>
            <div className="flex items-center gap-1 font-mono text-[11px] bg-zinc-800/80 px-2 py-0.5 rounded text-zinc-300 border border-zinc-700/50">
              <GitBranch className="h-3 w-3 text-emerald-400" />
              <span>repomedic/fix/issue-466</span>
            </div>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-2">
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Sandbox: Docker Container Isolated</span>
          </div>

          <a
            href="https://github.com/python-humanize/humanize/pull/467"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 transition-colors bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-1 rounded-md"
          >
            <span>PR #467</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      {/* Editor & Terminal Body */}
      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
        {/* Left Explorer Sidebar (3 cols) */}
        <div className="hidden lg:block lg:col-span-3 bg-[#0d1117] border-r border-zinc-800/80 p-3 select-none text-xs">
          <div className="text-[11px] uppercase tracking-wider font-mono font-semibold text-zinc-500 px-2 py-1 mb-1">
            Workspace Explorer
          </div>

          <div className="space-y-0.5">
            <div className="px-2 py-1.5 rounded flex items-center justify-between text-zinc-300 bg-zinc-800/50 font-medium">
              <div className="flex items-center gap-1.5 truncate">
                <FileCode className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                <span className="truncate">src/humanize/number.py</span>
              </div>
              <span className="text-[10px] font-mono font-bold text-amber-400">M</span>
            </div>

            <div className="px-2 py-1.5 rounded flex items-center justify-between text-zinc-400 hover:bg-zinc-800/30 transition-colors">
              <div className="flex items-center gap-1.5 truncate">
                <FileCode className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span className="truncate">tests/test_number.py</span>
              </div>
              <span className="text-[10px] font-mono font-bold text-emerald-400">+12</span>
            </div>

            <div className="px-2 py-1.5 rounded flex items-center gap-1.5 text-zinc-500">
              <FileCode className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
              <span>pyproject.toml</span>
            </div>

            <div className="px-2 py-1.5 rounded flex items-center gap-1.5 text-zinc-500">
              <FileCode className="h-3.5 w-3.5 text-purple-400 shrink-0" />
              <span>repomedic.yaml</span>
            </div>
          </div>

          {/* Symbol Outline */}
          <div className="mt-6 pt-4 border-t border-zinc-800/80">
            <div className="text-[11px] uppercase tracking-wider font-mono font-semibold text-zinc-500 px-2 py-1 mb-1">
              AST Symbol Graph
            </div>
            <div className="space-y-1 text-[11px] font-mono text-zinc-400 px-2">
              <div className="flex items-center gap-1 text-emerald-400">
                <ChevronRight className="h-3 w-3" />
                <span>intcomma(value, ndigits)</span>
              </div>
              <div className="pl-4 text-zinc-500 text-[10px]">
                <span>• lines 50-74</span>
              </div>
              <div className="flex items-center gap-1 text-cyan-400 mt-2">
                <ChevronRight className="h-3 w-3" />
                <span>test_negative_ndigits()</span>
              </div>
              <div className="pl-4 text-zinc-500 text-[10px]">
                <span>• synthesized regression</span>
              </div>
            </div>
          </div>

          {/* Verification Badge */}
          <div className="mt-8 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-bold">
              <ShieldCheck className="h-4 w-4" />
              <span>Zero Hallucination</span>
            </div>
            <p className="text-[11px] text-zinc-400 leading-tight">
              Strict gate enforced: 241/241 unit tests verified in isolated sandbox before PR dispatch.
            </p>
          </div>
        </div>

        {/* Main Work Area (9 cols) */}
        <div className="lg:col-span-9 flex flex-col justify-between bg-[#090d16]">
          {/* Work Area Tabs */}
          <div className="flex items-center justify-between border-b border-zinc-800 bg-[#0f141f] px-3">
            <div className="flex items-center">
              <button
                onClick={() => setActiveTab('diff')}
                className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'diff'
                    ? 'border-emerald-500 text-emerald-400 bg-zinc-800/40'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Code2 className="h-3.5 w-3.5" />
                <span>Unified Diff</span>
                <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded">
                  +3 / -0
                </span>
              </button>

              <button
                onClick={() => setActiveTab('pytest')}
                className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'pytest'
                    ? 'border-emerald-500 text-emerald-400 bg-zinc-800/40'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Terminal className="h-3.5 w-3.5" />
                <span>Sandbox Terminal</span>
                <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded">
                  241 PASS
                </span>
              </button>

              <button
                onClick={() => setActiveTab('cot')}
                className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'cot'
                    ? 'border-emerald-500 text-emerald-400 bg-zinc-800/40'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Cpu className="h-3.5 w-3.5" />
                <span>Nemotron 30B CoT</span>
              </button>

              <button
                onClick={() => setActiveTab('ast')}
                className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'ast'
                    ? 'border-emerald-500 text-emerald-400 bg-zinc-800/40'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                <span>Tree-sitter AST</span>
              </button>
            </div>

            {/* Terminal Actions */}
            {activeTab === 'pytest' && (
              <button
                onClick={handleRerunPytest}
                disabled={isTestRunning}
                className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
              >
                {isTestRunning ? (
                  <>
                    <RotateCcw className="h-3 w-3 animate-spin" />
                    <span>Running...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3 w-3 fill-current" />
                    <span>Re-run Pytest</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Tab Content Display */}
          <div className="p-4 sm:p-5 flex-1 overflow-x-auto font-mono text-xs leading-relaxed select-text">
            {/* TAB 1: CODE DIFF */}
            {activeTab === 'diff' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-[11px] text-zinc-400 pb-2 border-b border-zinc-800">
                  <span className="font-semibold text-zinc-200">src/humanize/number.py</span>
                  <span className="text-zinc-500">PatchValidator AST Check: PASSED</span>
                </div>

                <div className="space-y-0.5 text-zinc-300">
                  <div className="text-zinc-500">@@ -54,9 +54,12 @@ def intcomma(value, ndigits=None):</div>
                  <div className="text-zinc-400"> 54    """Converts an integer to a string containing commas every three digits."""</div>
                  <div className="text-zinc-400"> 55    if value is None:</div>
                  <div className="text-zinc-400"> 56        return None</div>
                  <div className="bg-emerald-500/15 text-emerald-300 px-2 py-0.5 rounded-sm border-l-2 border-emerald-400 flex items-center justify-between">
                    <span>+    if ndigits is not None and ndigits &lt; 0:</span>
                    <span className="text-[10px] text-emerald-400/80 font-sans font-medium">Input Validation Gate</span>
                  </div>
                  <div className="bg-emerald-500/15 text-emerald-300 px-2 py-0.5 rounded-sm border-l-2 border-emerald-400">
                    <span>+        raise ValueError(&quot;ndigits must be non-negative&quot;)</span>
                  </div>
                  <div className="text-zinc-400"> 59    orig = str(value)</div>
                  <div className="text-zinc-400"> 60    new = re.sub(r&quot;^(-?\d+)(\d&#123;3&#125;)&quot;, r&quot;\g&lt;1&gt;,\g&lt;2&gt;&quot;, orig)</div>
                  <div className="text-zinc-400"> 61    while new != orig:</div>
                </div>

                {/* Inline AI Explanation Card */}
                <div className="mt-4 p-3 rounded-lg bg-zinc-900/90 border border-emerald-500/30 text-xs text-zinc-300 font-sans space-y-1">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-xs">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>NVIDIA Nemotron 30B MoE Diagnosis</span>
                  </div>
                  <p className="text-[11px] text-zinc-400 leading-normal">
                    Previously, passing <code className="text-zinc-300 bg-zinc-800 px-1 py-0.5 rounded font-mono">ndigits=-1</code> propagated into Python float formatting <code className="text-zinc-300 bg-zinc-800 px-1 py-0.5 rounded font-mono">f&quot;.&#123;ndigits&#125;f&quot;</code>, raising <code className="text-red-400 font-mono">ValueError: Format specifier missing precision</code>. The boundary check safely raises a descriptive ValueError and preserves 100% backwards compatibility.
                  </p>
                </div>
              </div>
            )}

            {/* TAB 2: PYTEST TERMINAL */}
            {activeTab === 'pytest' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-zinc-500 text-[11px] pb-2 border-b border-zinc-800">
                  <span>Isolated Container Session (PID: 1042)</span>
                  <span>Sandbox: 0.20s</span>
                </div>

                {isTestRunning ? (
                  <div className="py-12 text-center space-y-3 font-sans">
                    <RotateCcw className="h-6 w-6 text-emerald-400 animate-spin mx-auto" />
                    <p className="text-xs text-zinc-300 font-mono">Running pytest tests/ inside isolated container...</p>
                    <div className="w-48 h-1.5 bg-zinc-800 rounded-full mx-auto overflow-hidden">
                      <div className="h-full bg-emerald-400 animate-pulse w-3/4" />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1 text-zinc-300 text-[11px]">
                    <div className="text-zinc-400 font-bold">root@sandbox:/workspace/humanize# pytest tests/test_number.py -v</div>
                    <div className="text-zinc-500">============================= test session starts ==============================</div>
                    <div className="text-zinc-500">platform linux -- Python 3.10.12, pytest-8.1.1, pluggy-1.4.0</div>
                    <div className="text-zinc-500">rootdir: /workspace/humanize, configfile: pyproject.toml</div>
                    <div className="text-zinc-500">collected 241 items</div>
                    <div className="pt-2 text-zinc-400">
                      tests/test_number.py::test_intcomma <span className="text-emerald-400 font-bold">PASSED [ 24%]</span>
                    </div>
                    <div className="text-emerald-300 font-semibold bg-emerald-500/10 px-1.5 py-0.5 rounded">
                      tests/test_number.py::test_intcomma_negative_ndigits <span className="text-emerald-400 font-bold">PASSED [ 25%]</span>
                    </div>
                    <div className="text-zinc-400">
                      tests/test_number.py::test_fractional <span className="text-emerald-400 font-bold">PASSED [ 26%]</span>
                    </div>
                    <div className="text-zinc-400">
                      tests/test_number.py::test_apnumber <span className="text-emerald-400 font-bold">PASSED [ 27%]</span>
                    </div>
                    <div className="text-zinc-500 pt-1">... [237 other tests passing] ...</div>
                    <div className="pt-3 text-emerald-400 font-bold border-t border-zinc-800 mt-2">
                      ======================== {testRunCount} passed in 0.20s ===========================
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: NEMOTRON 30B CoT REASONING */}
            {activeTab === 'cot' && (
              <div className="space-y-3 font-sans">
                <div className="flex items-center justify-between text-[11px] text-zinc-400 pb-2 border-b border-zinc-800 font-mono">
                  <span>Model: nvidia/nemotron-3.5-lightning-30b-a3b</span>
                  <span className="text-purple-400 font-bold">3,420 Thinking Tokens</span>
                </div>

                <div className="p-3.5 rounded-lg bg-zinc-950/80 border border-purple-500/30 text-xs font-mono space-y-2 text-zinc-300">
                  <span className="text-purple-400 font-bold text-[11px] block">
                    &lt;thought&gt; (Active Reasoning Chain)
                  </span>
                  <p className="text-zinc-300 leading-relaxed">
                    1. Target bug: Issue #466 states that passing negative ndigits raises ValueError: Format specifier missing precision.
                  </p>
                  <p className="text-zinc-300 leading-relaxed">
                    2. In Python 3.10+, string format specifier syntax <code className="bg-zinc-800 px-1 py-0.5 rounded font-mono">.&#123;precision&#125;f</code> expects a non-negative integer. If ndigits is negative (-1), Python parses it as an invalid specifier rather than rounding.
                  </p>
                  <p className="text-zinc-300 leading-relaxed">
                    3. Tree-sitter inspection shows intcomma in src/humanize/number.py handles value None but omitted ndigits bounds check.
                  </p>
                  <p className="text-zinc-300 leading-relaxed">
                    4. Synthesizing fix: Add guard `if ndigits is not None and ndigits &lt; 0: raise ValueError(...)`.
                  </p>
                  <p className="text-zinc-300 leading-relaxed">
                    5. Adding unit test in tests/test_number.py expecting pytest.raises(ValueError, match="ndigits must be non-negative").
                  </p>
                  <span className="text-purple-400 font-bold text-[11px] block">
                    &lt;/thought&gt;
                  </span>
                </div>
              </div>
            )}

            {/* TAB 4: TREE-SITTER AST */}
            {activeTab === 'ast' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between text-[11px] text-zinc-400 pb-2 border-b border-zinc-800">
                  <span>AST Slicer: tree-sitter-python</span>
                  <span className="text-cyan-400">1.4ms parse time</span>
                </div>

                <div className="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800 text-[11px] text-zinc-300 space-y-1">
                  <div>(module</div>
                  <div className="pl-3 text-cyan-400">(function_definition</div>
                  <div className="pl-6 text-emerald-400">name: (identifier) "intcomma"</div>
                  <div className="pl-6 text-zinc-400">parameters: (parameters</div>
                  <div className="pl-9 text-zinc-400">(identifier) "value"</div>
                  <div className="pl-9 text-zinc-400">(default_parameter (identifier) "ndigits" (none)))</div>
                  <div className="pl-6 text-zinc-400">body: (block</div>
                  <div className="pl-9 text-purple-400">(if_statement</div>
                  <div className="pl-12 text-zinc-300">condition: (comparison_operator) "ndigits &lt; 0"</div>
                  <div className="pl-12 text-zinc-300">consequence: (raise_statement (call "ValueError")))</div>
                  <div className="pl-9 text-zinc-500">... [remaining return statements] ...</div>
                  <div className="pl-3 text-cyan-400">)</div>
                  <div>)</div>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Telemetry Status Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-[#0d1117] border-t border-zinc-800 text-[11px] font-mono text-zinc-400 select-none">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Zero Hallucination Gate: PASSED</span>
              </span>
              <span className="hidden sm:inline text-zinc-600">|</span>
              <span className="hidden sm:inline">NVIDIA NIM Inference: 38.4 tok/s</span>
            </div>

            <div className="flex items-center gap-4">
              <span>AST: 1.4ms</span>
              <span className="text-zinc-600">|</span>
              <span className="text-emerald-400 font-bold">241/241 Tests Passing</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
