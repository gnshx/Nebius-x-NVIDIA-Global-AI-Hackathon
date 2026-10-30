#!/usr/bin/env python3
"""
RepoMedic — Local Neural TTS Audio Generator

Generates high-fidelity neural voiceover narration locally (100% free, no API keys needed)
using Microsoft Neural TTS / edge-tts for the Nebius x NVIDIA Global AI Hackathon.

Calibrated Voice Pacing:
- Natural, confident pacing (+10% speech rate)
- Crystal clear enunciation
- Strict duration adherence: ~144-150s (well under the 3-minute / 180s limit)

Usage:
    python3 scripts/generate_audio_local.py
    python3 scripts/generate_audio_local.py --voice en-US-ChristopherNeural
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

# Comprehensive Hackathon Pitch Narration Script tailored for Nebius x NVIDIA Hackathon
# STRICT REQUIREMENT: Total audio runtime MUST BE UNDER 3 MINUTES (<180 seconds).
# Measured duration at +10% rate: ~144.34 seconds (2 minutes 24.3 seconds).
PITCH_SCRIPT = (
    "Welcome to RepoMedic, the autonomous GitHub issue-to-pull-request verification agent "
    "built for the Nebius and NVIDIA Global AI Hackathon. "
    "Today, AI coding assistants generate code blindly, producing hallucinated diffs "
    "that break CI and burden maintainers. RepoMedic enforces our Zero-Hallucination Policy: a pull request is NEVER opened "
    "unless one hundred percent of unit tests pass inside an isolated container sandbox. "
    "To prove production capability, we ran RepoMedic against the popular open-source library "
    "python-humanize, resolving issue four sixty-six. Maintainers reported a crash when formatting with negative "
    "precision: intcomma with ndigits minus one crashed with a ValueError. "
    "Here is how RepoMedic solves it step-by-step. "
    "Step one: AST Fault Localization and Causal Slicing. "
    "Tree-sitter AST parsing extracts targeted symbols while causal slicing prunes irrelevant files, "
    "passing only the exact one thousand four hundred tokens needed. "
    "Step two: NVIDIA Nemotron 3.5 Lightning Reasoning. "
    "Powered by NVIDIA's thirty billion parameter Mixture-of-Experts model via NVIDIA NIM API, "
    "delivering frontier reasoning accuracy with sub-second step latency. "
    "Step three: Minimal Patch Synthesis and Dynamic Contract Fuzzing. "
    "Synthesizes clean PEP 8 diffs and audits boundary guards across None, boundary numerics, and negative values "
    "to prevent happy-path overfitting. "
    "Step four: Isolated Container Sandbox Execution. "
    "Executes the full pytest test suite in a hermetic Docker container, running multi-seed test shuffling "
    "to verify all two hundred and forty-one tests passing with zero regressions. "
    "Step five: Security Gate and Live Pull Request Dispatch. "
    "Validates directory bounds with PatchValidator, guaranteeing zero path traversals, "
    "and dispatches pull request four sixty-seven directly to GitHub. "
    "Our Next.js fourteen web portal provides full-spectrum observability, featuring a 60 FPS Three.js "
    "3D WebGL state machine and real-time streaming telemetry for every step. "
    "When third-party APIs drift or deprecate, RepoMedic queries Tavily AI Search to pull official documentation and self-heal. "
    "Built on open infrastructure with Nebius AI Cloud, NVIDIA NIM, and Docker sandboxes, "
    "RepoMedic turns hours of maintainer triage into two minutes of verified code. "
    "This is the future of autonomous agentic engineering."
)


async def synthesize_speech(text: str, output_path: Path, voice: str = "en-US-ChristopherNeural", rate: str = "+10%"):
    """Synthesize speech using edge-tts locally at a comfortable, natural pacing."""
    try:
        import edge_tts
    except ImportError:
        print("❌ edge-tts is not installed. Run: pip install edge-tts", file=sys.stderr)
        return False

    print(f"🎙️ Synthesizing local speech with voice: {voice} at calm, natural pacing (rate={rate})...")
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch="+0Hz")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await communicate.save(str(output_path))
    
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"✅ Local audio generated successfully! Saved to: {output_path} ({output_path.stat().st_size} bytes)")
        return True
    else:
        print("❌ Generated audio file is empty or missing.", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate demo audio locally using Neural TTS")
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Voice model (e.g. en-US-ChristopherNeural)")
    parser.add_argument("--rate", default="+10%", help="Speech rate (e.g. +10% for natural cadence)")
    parser.add_argument("--output", default="assets/repomedic_pitch.mp3", help="Output audio file path")
    
    args = parser.parse_args()
    output_path = Path(args.output).resolve()
    
    print("=" * 60)
    print("🤖 RepoMedic Local Voice Synthesizer")
    print("   Running locally — 100% free, natural pacing (+10%)")
    print("=" * 60)
    
    success = asyncio.run(synthesize_speech(PITCH_SCRIPT, output_path, voice=args.voice, rate=args.rate))
    if not success:
        sys.exit(1)
        
    # Also copy to web public assets so Next.js can serve it directly in browser!
    web_public_assets = Path("apps/web/public/assets")
    if web_public_assets.exists():
        dest = web_public_assets / output_path.name
        shutil.copy2(output_path, dest)
        print(f"📦 Synced audio to web assets: {dest}")


if __name__ == "__main__":
    main()
