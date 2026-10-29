#!/usr/bin/env python3
"""
RepoMedic — ElevenLabs Demo Audio Generator

Generates high-fidelity professional voiceover narration for the Nebius x NVIDIA
Global AI Hackathon submission video.

Usage:
    python3 scripts/generate_audio_elevenlabs.py --api-key YOUR_ELEVENLABS_KEY
    # Or set ELEVENLABS_API_KEY in .env
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

# Professional Hackathon Presentation Narration Script
PITCH_SCRIPT = (
    "Welcome to RepoMedic, the autonomous GitHub issue-to-pull-request verification agent "
    "built for the Nebius and NVIDIA Global AI Hackathon. "
    "Today, AI coding assistants generate code blindly, frequently producing hallucinated diffs "
    "that break continuous integration and burden open-source maintainers. "
    "RepoMedic solves this with a strict guarantee: zero hallucinated PRs. "
    "A pull request is never opened unless one hundred percent of unit and regression tests pass "
    "inside an isolated execution sandbox. "
    "At the heart of RepoMedic is NVIDIA Nemotron 3.5 Lightning, a thirty billion parameter "
    "Mixture-of-Experts model running via NVIDIA NIM API. "
    "By activating just three-point-five billion parameters per token, Nemotron delivers lightning-fast "
    "step latencies under one-point-five seconds while generating full chain-of-thought reasoning traces. "
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


def generate_audio(api_key: str, output_path: Path, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
    """Call ElevenLabs API via standard urllib to generate MP3 audio."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    
    payload = {
        "text": PITCH_SCRIPT,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }
    
    print(f"🎙️ Sending narration script ({len(PITCH_SCRIPT)} chars) to ElevenLabs API...")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            audio_data = response.read()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(audio_data)
            print(f"✅ Audio successfully generated! Saved to: {output_path} ({len(audio_data)} bytes)")
            return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"❌ ElevenLabs API error ({e.code}): {err_msg}", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"❌ Failed to generate audio: {exc}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate demo audio with ElevenLabs")
    parser.add_argument("--api-key", default=os.getenv("ELEVENLABS_API_KEY", ""), help="ElevenLabs API Key")
    parser.add_argument("--voice-id", default="21m00Tcm4TlvDq8ikWAM", help="ElevenLabs Voice ID (default: Rachel)")
    parser.add_argument("--output", default="assets/repomedic_pitch.mp3", help="Output audio file path")
    
    args = parser.parse_args()
    api_key = args.api_key.strip()
    
    # Check .env if key not provided
    if not api_key:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        print("⚠️ No ElevenLabs API key provided.")
        print("Please run with:")
        print("    python3 scripts/generate_audio_elevenlabs.py --api-key YOUR_KEY")
        print("\nOr add ELEVENLABS_API_KEY=your_key to .env")
        sys.exit(1)

    out_path = Path(args.output).resolve()
    success = generate_audio(api_key, out_path, voice_id=args.voice_id)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
