---
name: hackathon-winner
description: Comprehensive playbook and evaluation matrix for winning AI hackathons (Devpost, Nebius, NVIDIA). Focuses on maximizing scoring across all 4 criteria (Technology 25%, Design 25%, Impact 25%, Idea 25%), crafting 30-second 'Aha' moments, and ensuring zero technical vulnerabilities.
---

# Hackathon Winner Playbook

This skill guides teams to victory in competitive AI hackathons by aligning directly with judge evaluation rubrics, psychology, and submission standards.

## 1. The 4 Criteria Evaluation Engine (25% Each)

### Criterion 1: Technological Implementation (25%)
- **NVIDIA & Nebius Stack Native Integration:** Must visibly utilize NVIDIA Nemotron (30B MoE) via NVIDIA NIM API and Nebius infrastructure.
- **Closed-Loop Execution:** Agents must not just *write* code; they must *execute*, *test*, and *verify* in hermetic container sandboxes.
- **Deep Algorithmic Rigor:** Feature SOTA techniques (Tree-sitter AST slicing, multi-seed test shuffling, property fuzzing, memory leak guards).
- **Zero Mock / Zero Fake Policy:** Real API keys, real container execution, real GitHub APIs.

### Criterion 2: Design & User Experience (25%)
- **Beyond Plain Terminal:** Deliver a cohesive, stunning web application (Next.js 14 App Router, dark slate aesthetic, glassmorphism).
- **Interactive 3D Visualizer:** Three.js 60 FPS WebGL state machine rendering agent nodes and real-time data flows.
- **Live Observability:** Server-Sent Events (SSE) streaming node state, tokens, duration, and diff inspectors.
- **Zero Friction Onboarding:** Immediate interactive demo with pre-populated real-world examples.

### Criterion 3: Potential Impact (25%)
- **Solve Real Developer Pain:** Target the #1 crisis in AI coding: 73% of AI-generated PRs break CI or cause regressions.
- **Real Open-Source Proof:** Prove the solution on an authentic repository with 2,500+ stars (`python-humanize/humanize #466` -> PR `#467`).
- **Quantifiable ROI:** Contrast 45 minutes of manual developer triage with 48 seconds of autonomous, test-verified repair.

### Criterion 4: Quality of the Idea (25%)
- **The "Uncompromising Policy" Moat:** The Zero-Hallucination Policy (a PR is NEVER opened unless 100% of unit tests pass in sandbox).
- **Causal Slicing vs. Token Dumping:** Contrast naive 50,000-line LLM prompts with surgical 1,420-token Tree-sitter AST slices.
- **Enterprise-Ready:** Pre-flight security auditing (PatchValidator) to prevent code injection and directory traversal.

---

## 2. The 3-Minute Demo Video Formula

Judges watch 50+ videos back-to-back. Adhere strictly to this timing arc:
1. **0:00 - 0:25 (Hook & Stakes):** Show the pain immediately (broken CI, red test failures, developer exhaustion). Introduce RepoMedic and the Zero-Hallucination Policy.
2. **0:25 - 0:50 (Real-World Evidence):** Feature an authentic open-source issue (`python-humanize #466`) rather than toy synthetic examples.
3. **0:50 - 1:45 (Process & Innovation):** Walk through the 12-node pipeline using the 4-part framework:
   - WHAT each step does
   - HOW it does it (Tree-sitter, NVIDIA Nemotron 30B MoE NIM, dynamic fuzzing, Docker sandbox)
   - WHY it does it (prevents hallucinations, guarantees sound logic)
   - WHY IT IS BEST (sub-second latency, surgical token bounds)
4. **1:45 - 2:20 (Live Results & Telemetry):** Show the real GitHub PR #467, 241 passed tests, and the Next.js 14 observability portal.
5. **2:20 - 2:45 (Conclusion & Call to Action):** Reiterate the open infrastructure stack (Nebius + NVIDIA NIM) and invite judges to test the live demo.

---

## 3. Devpost Submission Checklist

- [ ] **Descriptive Title:** Project Name + Punchy Tagline.
- [ ] **Inspiration Section:** Why blind AI code generation is broken.
- [ ] **What It Does:** Clear, high-level non-technical summary.
- [ ] **How We Built It:** Detailed technical architecture (LangGraph, Nemotron, NIM API, Docker, Next.js, Three.js).
- [ ] **Challenges We Ran Into:** Authentic engineering struggles (AST context slicing, test flakiness, container isolation).
- [ ] **Accomplishments That We're Proud Of:** Real PR #467 on python-humanize, 241/241 tests passed, 256 unit tests.
- [ ] **What We Learned:** MoE activation dynamics, deterministic test oracles.
- [ ] **What's Next for RepoMedic:** Multi-language LSP integration, autonomous benchmarking.
- [ ] **Links:** GitHub Repository, Live Demo URL, 1080p Video Embed.
