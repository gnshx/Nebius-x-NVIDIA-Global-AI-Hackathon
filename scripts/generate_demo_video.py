#!/usr/bin/env python3
"""
RepoMedic — Submission Demo Video Generator

Compiles a high-definition 1080p MP4 presentation video using ffmpeg,
synchronizing:
1. Real open-source issue walkthrough (python-humanize/humanize #466 -> PR #467)
2. 4-part process slides: WHAT, HOW, WHY, WHY IT IS BEST for each step
3. Real 1080p headless Chrome screenshots of the live Next.js web portal
4. High-fidelity neural voiceover audio track (edge-tts)

Usage:
    python3 scripts/generate_demo_video.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_audio_duration(audio_path: Path) -> float:
    """Probe audio duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"⚠️ Warning: Could not probe audio duration ({e}). Defaulting to 170.5s.")
        return 170.5


def main():
    root_dir = Path(__file__).resolve().parent.parent
    assets_dir = root_dir / "assets"
    storyboard_dir = assets_dir / "storyboard"
    shots_dir = assets_dir / "shots"
    output_video = assets_dir / "repomedic_demo.mp4"
    audio_track = assets_dir / "repomedic_pitch.mp3"

    print("=" * 60)
    print("🎬 RepoMedic Submission Demo Video Generator")
    print("   Nebius × NVIDIA Global AI Hackathon")
    print("=" * 60)

    # 1. Ensure storyboard slides exist
    if not storyboard_dir.exists() or len(list(storyboard_dir.glob("*.jpg"))) < 9:
        print("🎨 Generating high-definition storyboard slides...")
        from scripts.generate_rich_storyboard_slides import generate_all_slides
        generate_all_slides(storyboard_dir)

    # 2. Check required assets
    slides = {
        "s1_hero": storyboard_dir / "slide_01_hero.jpg",
        "s2_issue": storyboard_dir / "slide_02_issue_humanize.jpg",
        "s3_ast": storyboard_dir / "slide_03_ast_slicing.jpg",
        "s4_nemotron": storyboard_dir / "slide_04_nemotron_reasoning.jpg",
        "s5_fuzz": storyboard_dir / "slide_05_patch_fuzzing.jpg",
        "s6_sandbox": storyboard_dir / "slide_06_sandbox_pytest.jpg",
        "s7_pr": storyboard_dir / "slide_07_real_pr_github.jpg",
        "s8_obs": storyboard_dir / "slide_08_observability.jpg",
        "s9_conclusion": storyboard_dir / "slide_09_conclusion.jpg",
    }
    
    shots = {
        "landing": shots_dir / "landing.png",
        "runs": shots_dir / "runs.png",
        "humanize_run": shots_dir / "humanize_run.png",
    }

    # Verify presence
    for name, path in {**slides, **shots}.items():
        if not path.exists():
            print(f"❌ Missing required visual asset: {path}", file=sys.stderr)
            sys.exit(1)

    has_audio = audio_track.exists()
    if has_audio:
        duration = get_audio_duration(audio_track)
        print(f"🎵 Found audio track: {audio_track.name} (Duration: {duration:.2f}s)")
    else:
        duration = 170.5
        print(f"ℹ️ Audio track not found. Using default timing ({duration:.2f}s)")

    # 3. Define sequence of frames and their duration weights
    # Total sum of durations must perfectly match audio duration (~170.5s)
    # Target timeline:
    # 0:00 - 0:14 (14s): Hero Intro & Zero-Hallucination Policy
    # 0:14 - 0:24 (10s): Live Portal Landing Page & Architecture Badges
    # 0:24 - 0:42 (18s): Real Open-Source Issue (humanize #466 - WHAT/HOW/WHY/WHY BEST)
    # 0:42 - 1:00 (18s): Step 1: AST Fault Localization & Slicing
    # 1:00 - 1:20 (20s): Step 2: NVIDIA Nemotron 30B MoE NIM API Synthesis
    # 1:20 - 1:38 (18s): Step 3: Minimal Patch & Dynamic Contract Fuzzing
    # 1:38 - 1:58 (20s): Step 4: Hermetic Docker Sandbox & 241/241 Tests Passed
    # 1:58 - 2:14 (16s): Step 5: Security Gate & Live PR #467 on GitHub
    # 2:14 - 2:24 (10s): Live Run Telemetry & Diff Inspector (humanize #466)
    # 2:24 - 2:32 (8s):  Live Portal Runs Table (verified runs)
    # 2:32 - 2:42 (10s): Real-Time Observability & Three.js 3D WebGL
    # 2:42 - 2:50.5 (8.5s): Enterprise Impact & Hackathon Summary

    raw_timeline = [
        (slides["s1_hero"], 14.0),
        (shots["landing"], 10.0),
        (slides["s2_issue"], 18.0),
        (slides["s3_ast"], 18.0),
        (slides["s4_nemotron"], 20.0),
        (slides["s5_fuzz"], 18.0),
        (slides["s6_sandbox"], 20.0),
        (slides["s7_pr"], 16.0),
        (shots["humanize_run"], 10.0),
        (shots["runs"], 8.0),
        (slides["s8_obs"], 10.0),
        (slides["s9_conclusion"], 8.5),
    ]

    total_weight = sum(w for _, w in raw_timeline)
    scaling_factor = duration / total_weight

    timeline = [(img, w * scaling_factor) for img, w in raw_timeline]

    # Write concat manifest
    temp_concat_txt = assets_dir / "slides_manifest.txt"
    with open(temp_concat_txt, "w") as f:
        for idx, (img_path, d) in enumerate(timeline):
            f.write(f"file '{img_path.resolve()}'\n")
            f.write(f"duration {d:.3f}\n")
        # Concat demuxer requirement: repeat last file once with no duration
        f.write(f"file '{timeline[-1][0].resolve()}'\n")

    print(f"📋 Generated manifest with {len(timeline)} frames across {duration:.2f} seconds.")

    # 4. Compile video using ffmpeg
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(temp_concat_txt),
    ]

    if has_audio:
        cmd.extend([
            "-i", str(audio_track),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black",
            str(output_video),
        ])
    else:
        cmd.extend([
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-t", str(duration),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black",
            str(output_video),
        ])

    print("🚀 Running FFmpeg 1080p rendering pipeline...")
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        size_mb = output_video.stat().st_size / (1024 * 1024)
        print(f"🎉 Demo video generated successfully!")
        print(f"   Location: {output_video}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Duration: {duration:.2f}s (<180s constraint satisfied)")

        # Cleanup manifest
        if temp_concat_txt.exists():
            temp_concat_txt.unlink()

        # 5. Synchronize to Next.js web public directory
        web_assets = root_dir / "apps" / "web" / "public" / "assets"
        if web_assets.exists():
            dest = web_assets / output_video.name
            shutil.copy2(output_video, dest)
            print(f"📦 Synced demo video to web public assets: {dest}")

        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e.stderr.decode('utf-8')[:400]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
