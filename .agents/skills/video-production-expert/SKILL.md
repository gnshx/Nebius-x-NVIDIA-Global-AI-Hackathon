---
name: video-production-expert
description: Expert methodology for producing high-retention, high-converting developer demo videos for AI hackathons and product launches. Covers storyboard sequencing, audio narration synchronization, FFmpeg automated rendering, and Devpost embedding best practices.
---

# Video Production Expert Playbook

This skill provides actionable standards for scripting, recording, compiling, and delivering award-winning technical demonstration videos.

## 1. Technical Video Standards
- **Resolution:** Strictly 1920×1080 (1080p Full HD) or 3840×2160 (4K).
- **Aspect Ratio:** 16:9 widescreen.
- **Framerate:** 30 fps or 60 fps progressive (`yuv420p` pixel format for universal compatibility).
- **Audio Codec:** AAC at 192 kbps or higher, 48 kHz stereo.
- **Duration Constraint:** Strictly under the hackathon limit (typically 3 minutes max / 180 seconds). Aim for 2m 30s to 2m 50s.

## 2. Visual Layering Strategy
Never rely on a single visual mode:
1. **Rich Storyboard Infographics (40%):** Clean dark-slate slides breaking down architecture, formulas, and AST trees.
2. **Real Terminal & Code Diffs (30%):** Actual terminal output (`pytest 241 passed in 0.20s`), colorized unified diffs, and AST S-expressions.
3. **Live Web Application Screen Captures (30%):** Headless Chrome 1080p full-bleed captures showing interactive UI, 3D WebGL canvases, and live telemetry.

## 3. Pacing & Script Pacing
- **Speech Rate:** 140–160 words per minute. Confident, authoritative, technical.
- **Tone:** Technical, rigorous, zero marketing fluff, zero unsubstantiated claims.
- **Visual Transitions:** Switch or animate visual frames every 8 to 18 seconds to maintain cognitive engagement.

## 4. Automated Compilation Pipeline via FFmpeg
Automate video generation with reproducible Python scripts (`scripts/generate_demo_video.py`):
```bash
ffmpeg -y -f concat -safe 0 -i slides_manifest.txt \
       -i audio_narration.mp3 \
       -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 \
       -c:a aac -b:a 192k -shortest \
       -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black" \
       output_demo.mp4
```

## 5. Web Player Integration
- Provide HTML5 `<video>` embedding with byte-range streaming (`Accept-Ranges: bytes`).
- Implement interactive chapter markers allowing judges to jump directly to specific milestones (e.g., Real Bug, Nemotron 30B MoE, Docker Sandbox, Live PR).
- Offer direct 1080p MP4 download links alongside the player.
