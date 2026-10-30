# Devpost Final Submission Checklist & Quick Guide

Follow these steps to submit RepoMedic to the **Nebius x NVIDIA Global AI Hackathon**:

---

## 1. Devpost Submission Fields (Copy & Paste from `DEVPOST_SUBMISSION.md`)

- **Project Name:**  
  `RepoMedic — Autonomous Closed-Loop Program Repair Agent`

- **Elevator Pitch / Tagline:**  
  `Zero-hallucination autonomous program repair agent powered by NVIDIA Nemotron 30B MoE via NVIDIA NIM & hermetic container execution. Diagnoses bugs, generates AST-causal fixes, and verifies 100% test passing before opening PRs.`

- **Submission Track:**  
  `Coding & Agentic Engineering (NVIDIA & Nebius Track)`

- **GitHub Repository URL:**  
  `https://github.com/gnshx/Nebius-x-NVIDIA-Global-AI-Hackathon`

- **Video Demo URL:**  
  Upload `repomedic/assets/repomedic_demo.mp4` to YouTube (Unlisted or Public) or Loom/Vimeo, and paste the URL in Devpost.  
  *(The video file is located at `repomedic/assets/repomedic_demo.mp4`, 1920x1080 Full HD, 144.3s duration, 4.12 MB).*

- **Story & Description:**  
  Copy the full markdown from `repomedic/DEVPOST_SUBMISSION.md` directly into the "About the Project" text area.

- **Built With Tags:**  
  `python, nvidia-nim, nemotron-3-moe, nebius, docker, langgraph, fastapi, tree-sitter, nextjs, threejs, tailwind-css, typescript`

---

## 2. Key Links to Highlight for Judges

- **GitHub Repo:** [https://github.com/gnshx/Nebius-x-NVIDIA-Global-AI-Hackathon](https://github.com/gnshx/Nebius-x-NVIDIA-Global-AI-Hackathon)
- **Real Open-Source PR Proof:** [https://github.com/python-humanize/humanize/pull/467](https://github.com/python-humanize/humanize/pull/467)
- **Real Open-Source Issue:** [https://github.com/python-humanize/humanize/issues/466](https://github.com/python-humanize/humanize/issues/466)
- **Local Web App:** `http://localhost:3000/`

---

## 3. Pre-Flight Verification Evidence

- ✅ **Pytest:** 256 / 256 unit tests passed in 0.81s (`pytest`).
- ✅ **Truthfulness Audit:** 0 violations detected (`python3 scripts/verify_truthfulness.py`).
- ✅ **Frontend Build:** 100% successful compilation with 0 lint or type errors (`npm run build`).
- ✅ **Demo Video:** 144.34s (under 3-minute hard limit), 1080p Full HD, AAC 192k audio.
- ✅ **Git Status:** Clean tree, fully synced with `origin/main` on GitHub.
