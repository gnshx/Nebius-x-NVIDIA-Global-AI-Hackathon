'use client';

import React, { useState } from 'react';
import { 
  Play, 
  Sparkles, 
  CheckCircle2, 
  ExternalLink, 
  Download, 
  Cpu, 
  ShieldCheck, 
  Layers, 
  Terminal,
  Clock,
  Video
} from 'lucide-react';

interface Chapter {
  timestamp: string;
  seconds: number;
  title: string;
  description: string;
  badge: string;
  badgeColor: string;
}

const CHAPTERS: Chapter[] = [
  {
    timestamp: "0:00",
    seconds: 0,
    title: "The Closed-Loop Paradigm",
    description: "Zero-Hallucination Policy: PRs strictly blocked unless 100% unit tests pass.",
    badge: "Problem & Standard",
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
  },
  {
    timestamp: "0:20",
    seconds: 20,
    title: "Real Bug: python-humanize #466",
    description: "Authentic maintainer bug on 2,500+ ★ repo: intcomma() crashes on negative ndigits.",
    badge: "Real Open Source",
    badgeColor: "text-red-400 bg-red-500/10 border-red-500/20"
  },
  {
    timestamp: "0:36",
    seconds: 36,
    title: "Step 1: AST Fault Localization",
    description: "Tree-sitter AST parsing isolates 1,420 token slice, eliminating context dilution.",
    badge: "WHAT / HOW / WHY / BEST",
    badgeColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20"
  },
  {
    timestamp: "0:51",
    seconds: 51,
    title: "Step 2: Nemotron 30B MoE Reasoning",
    description: "NVIDIA NIM API activates 3.5B params/token with sub-second streaming chain-of-thought.",
    badge: "NVIDIA NIM",
    badgeColor: "text-purple-400 bg-purple-500/10 border-purple-500/20"
  },
  {
    timestamp: "1:07",
    seconds: 67,
    title: "Step 3: Contract Fuzzing & Diffs",
    description: "Dynamic parameter boundary fuzzing across None, boundary numerics, and negative values.",
    badge: "SWE-Fuzz 2026",
    badgeColor: "text-amber-400 bg-amber-500/10 border-amber-500/20"
  },
  {
    timestamp: "1:22",
    seconds: 82,
    title: "Step 4: Hermetic Sandbox Pytest",
    description: "241 / 241 unit tests pass in isolated Docker sandbox with multi-seed test shuffling.",
    badge: "100% Pass Proof",
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
  },
  {
    timestamp: "1:39",
    seconds: 99,
    title: "Step 5: Live Pull Request #467",
    description: "PatchValidator security check and authenticated dispatch to GitHub repository.",
    badge: "Live GitHub PR",
    badgeColor: "text-blue-400 bg-blue-500/10 border-blue-500/20"
  },
  {
    timestamp: "1:52",
    seconds: 112,
    title: "Live Observability & 3D WebGL",
    description: "Real-time Next.js portal with Three.js state machine visualizer and SSE telemetry.",
    badge: "Next.js + Three.js",
    badgeColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20"
  },
  {
    timestamp: "2:10",
    seconds: 130,
    title: "Conclusion & Open Infrastructure",
    description: "Turning hours of maintainer triage into 2 minutes of test-verified code.",
    badge: "Enterprise Impact",
    badgeColor: "text-purple-400 bg-purple-500/10 border-purple-500/20"
  }
];

export function DemoVideoPlayer() {
  const [activeChapter, setActiveChapter] = useState<number>(0);
  const videoRef = React.useRef<HTMLVideoElement>(null);

  const seekTo = (seconds: number, index: number) => {
    setActiveChapter(index);
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(() => {});
    }
  };

  return (
    <section id="demo-video" className="rounded-2xl border border-zinc-800 bg-card/60 backdrop-blur-xl p-6 sm:p-8 space-y-6 shadow-2xl relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 blur-[100px] pointer-events-none rounded-full" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-emerald-500/10 blur-[100px] pointer-events-none rounded-full" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Video className="h-3 w-3" />
              Official Hackathon Submission Video
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-800 text-zinc-300">
              <Clock className="h-3 w-3 text-zinc-400" />
              2m 24s (1080p 30fps)
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Autonomous Issue-to-PR Walkthrough
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Featuring real open-source case study <strong className="text-foreground">python-humanize #466</strong> and step-by-step breakdown (WHAT, HOW, WHY, WHY IT IS BEST).
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <a
            href="https://github.com/python-humanize/humanize/pull/467"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-800/80 hover:bg-zinc-700/80 text-zinc-200 border border-zinc-700/60 transition-all"
          >
            <ExternalLink className="h-3.5 w-3.5 text-blue-400" />
            Verified PR #467
          </a>
          <a
            href="/assets/repomedic_demo.mp4"
            download="repomedic_demo_1080p.mp4"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-zinc-950 transition-all shadow-sm"
          >
            <Download className="h-3.5 w-3.5" />
            Download 1080p MP4
          </a>
        </div>
      </div>

      {/* Video Player Box */}
      <div className="relative rounded-xl overflow-hidden border border-zinc-800 bg-black/90 shadow-2xl aspect-video group">
        <video
          ref={videoRef}
          controls
          preload="metadata"
          className="w-full h-full object-contain"
          src="/assets/repomedic_demo.mp4"
        >
          Your browser does not support the video tag.
        </video>
      </div>

      {/* Interactive Chapter Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
          <span className="flex items-center gap-1.5 text-zinc-300 font-semibold">
            <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
            Interactive Process Chapters (Click to Jump)
          </span>
          <span>Click any milestone to jump directly</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {CHAPTERS.map((chapter, idx) => (
            <button
              key={idx}
              onClick={() => seekTo(chapter.seconds, idx)}
              className={`text-left p-3 rounded-lg border transition-all text-xs space-y-1.5 ${
                activeChapter === idx
                  ? 'border-emerald-500/60 bg-emerald-500/10 shadow-sm'
                  : 'border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-800/50 hover:border-zinc-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-emerald-400">{chapter.timestamp}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${chapter.badgeColor}`}>
                  {chapter.badge}
                </span>
              </div>
              <div className="font-semibold text-zinc-200 line-clamp-1">{chapter.title}</div>
              <div className="text-[11px] text-zinc-400 line-clamp-2 leading-relaxed">{chapter.description}</div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
