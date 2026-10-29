#!/usr/bin/env python3
"""
RepoMedic — Local Neural TTS Audio Generator

Generates high-fidelity neural voiceover narration locally (100% free, no API keys needed)
using Microsoft Neural TTS / edge-tts for the Nebius x NVIDIA Global AI Hackathon.

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

# Professional Hackathon Pitch Narration Script tailored for Nebius x NVIDIA Hackathon
PITCH_SCRIPT = (
    "Welcome to RepoMedic, the autonomous GitHub issue-to-pull-request verification agent "
    "built for the Nebius and NVIDIA Global AI Hackathon. "
    "Today, AI coding assistants generate code blindly, frequently producing hallucinated diffs "
    "that break continuous integration and burden open-source maintainers. "
    "RepoMedic solves this with an absolute guarantee: zero hallucinated PRs. "
    "A pull request is never opened unless one hundred percent of unit and regression tests pass "
    "inside an isolated execution sandbox. "
    "At the heart of RepoMedic is NVIDIA Nemotron 3.5 Lightning, a thirty billion parameter "
    "Mixture-of-Experts model running on the Nebius Token Factory. "
    "By activating three-point-five billion parameters per token, Nemotron delivers sub-second "
    "step latencies while generating full chain-of-thought reasoning traces. "
    "RepoMedic orchestrates twelve LangGraph state machine nodes: ingesting issues, parsing repository syntax "
    "with Tree-sitter AST chunking, synthesizing targeted regression tests, and enforcing strict security checks "
    "with PatchValidator to prevent path traversal or credential exposure. "
    "To prove real-world production capability, we ran RepoMedic against the popular open-source library "
    "python-humanize, resolving issue four sixty-six. "
    "Nemotron diagnosed a missing precision validation in intcomma, generated an elegant fix, "
    "and verified all two hundred and forty-one tests passing with zero regressions before dispatching the pull request. "
    "When third-party dependencies drift or APIs deprecate, RepoMedic selectively queries Tavily AI Search "
    "to pull official migration docs and self-heal automatically. "
    "With a real-time Next.js observability portal, RepoMedic turns hours of maintainer triage into sixty seconds "
    "of verified confidence. This is the future of autonomous agentic engineering on open infrastructure."
)


async def synthesize_speech(text: str, output_path: Path, voice: str = "en-US-ChristopherNeural"):
    """Synthesize speech using edge-tts locally."""
    try:
        import edge_tts
    except ImportError:
        print("❌ edge-tts is not installed. Run: pip install edge-tts", file=sys.stderr)
        return False

    print(f"🎙️ Synthesizing local speech with voice: {voice}...")
    communicate = edge_tts.Communicate(text, voice, rate="+2%", pitch="+0Hz")
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
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Voice model (e.g. en-US-ChristopherNeural, en-US-AndrewMultilingualNeural)")
    parser.add_argument("--output", default="assets/repomedic_pitch.mp3", help="Output audio file path")
    
    args = parser.parse_args()
    output_path = Path(args.output).resolve()
    
    print("=" * 60)
    print("🤖 RepoMedic Local Voice Synthesizer")
    print("   Running locally — 100% free, no external API keys required")
    print("=" * 60)
    
    success = asyncio.run(synthesize_speech(PITCH_SCRIPT, output_path, voice=args.voice))
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
