---
name: video-storytelling
description: Advanced engineering playbook for creating high-retention technical demonstration videos. Synthesizes principles from Remotion, motion design, cognitive load management, and psychological pacing for developer and judge audiences.
---

# Video Storytelling & Technical Motion Playbook

This skill governs the production of high-impact, high-clarity demonstration videos for developer-centric products and competitive hackathons.

## 1. The Cognitive Retention Matrix

Technical audiences lose interest when presentations are either too superficial (marketing vaporware) or too dense (unexplained code walls). The optimal structure balances conceptual hierarchy with empirical proof:

| Video Phase | Cognitive Objective | Visual Vehicle | Duration | Pacing |
| :--- | :--- | :--- | :--- | :--- |
| **01. Hook & Tension** | Establish immediate stakes | Broken CI screenshot, red traceback | 0:00 - 0:25 | Fast (160 wpm) |
| **02. Real Proof Intro** | Prove authenticity | Real GitHub Issue (`humanize #466`) | 0:25 - 0:50 | Steady |
| **03. Process Architecture** | Explain engineering depth | 12-node pipeline diagram (WHAT/HOW/WHY) | 0:50 - 1:45 | Methodical |
| **04. Live Verification** | Show hermetic validation | Docker terminal, 241 passed tests | 1:45 - 2:20 | Confident |
| **05. Call to Action** | Seal the impression | Open source PR #467 + Live Web UI | 2:20 - 2:50 | Inspiring |

## 2. The 4-Part Node Explanation Framework

For every pipeline step shown in technical videos, never state just what the component is. Address all four cognitive pillars:
1. **WHAT:** The specific operation performed (e.g., Causal Program Slicing).
2. **HOW:** The exact technology used (e.g., Tree-sitter AST extraction of caller-callee subgraphs).
3. **WHY:** The failure mode prevented (e.g., stops context dilution and 50k token budget waste).
4. **WHY IT IS BEST:** The quantitative benchmark (e.g., 85% token reduction, sub-50ms parse time).

## 3. Visual Layering Rules
- **No Static Screen:** Change the focal point or slide frame at least once every 12-15 seconds.
- **Side-by-Side Unified Diffs:** Show green additions and red deletions clearly formatted with syntax highlighting.
- **Terminal Authenticity:** Include genuine terminal logs (`pytest`, `docker run`) rather than mocked console output.
- **Synchronized Audio & Subtitles:** Ensure voice narration triggers right as the corresponding visual slide or terminal appears.
