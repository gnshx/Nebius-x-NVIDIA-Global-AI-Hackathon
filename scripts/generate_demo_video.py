#!/usr/bin/env python3
"""
RepoMedic — Submission Demo Video Generator

Compiles a high-definition 1080p MP4 presentation video using ffmpeg,
synchronizing visual slides, system architecture diagrams, and the
neural audio narration track.

Usage:
    python3 scripts/generate_demo_video.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main():
    root_dir = Path(__file__).resolve().parent.parent
    assets_dir = root_dir / "assets"
    output_video = assets_dir / "repomedic_demo.mp4"
    audio_track = assets_dir / "repomedic_pitch.mp3"
    
    arch_img = assets_dir / "architecture.jpg"
    dash_img = assets_dir / "dashboard.jpg"
    
    if not arch_img.exists() or not dash_img.exists():
        print("❌ Required images missing in assets/ (architecture.jpg or dashboard.jpg)", file=sys.stderr)
        sys.exit(1)

    print("🎬 Generating RepoMedic Presentation Video via FFmpeg...")

    # Check if audio exists
    has_audio = audio_track.exists()
    if has_audio:
        print(f"🎵 Found audio track: {audio_track}")
    else:
        print("ℹ️ Audio track not found. Video will be generated with visual transitions.")
        print("   Run `python3 scripts/generate_audio_local.py` first to add audio.")

    # Slides timing and images
    # We will build a video loop showing:
    # 0-10s: Architecture infographic
    # 10-25s: Dashboard overview
    # 25-45s: Architecture deep-dive
    # 45-70s: Dashboard test verification proof
    # Repeated or matched to audio duration
    
    # Simple, high-quality ffmpeg command to create 1080p video from slides
    temp_concat_txt = assets_dir / "slides.txt"
    with open(temp_concat_txt, "w") as f:
        f.write(f"file '{arch_img}'\nduration 15\n")
        f.write(f"file '{dash_img}'\nduration 20\n")
        f.write(f"file '{arch_img}'\nduration 20\n")
        f.write(f"file '{dash_img}'\nduration 25\n")
        f.write(f"file '{arch_img}'\nduration 20\n")
        f.write(f"file '{dash_img}'\nduration 25\n")
        f.write(f"file '{arch_img}'\n")

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
            "-t", "65",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black",
            str(output_video),
        ])

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"🎉 Demo video generated successfully! Saved to: {output_video}")
        if temp_concat_txt.exists():
            temp_concat_txt.unlink()
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e.stderr.decode('utf-8')[:300]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
