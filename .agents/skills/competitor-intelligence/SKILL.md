---
name: competitor-intelligence
description: Systematic framework for evaluating hackathon competitors and market alternatives. Identifies architectural weaknesses, benchmarks feature completeness, and crafts defensible moats.
---

# Competitor Intelligence Framework

This skill benchmarks competing AI agent implementations to identify vulnerabilities, highlight unique advantages, and position RepoMedic as the clear winner.

## 1. Competitor Classification in Coding Tracks

| Archetype | Common Architecture | Fatal Vulnerability | How RepoMedic Wins |
| :--- | :--- | :--- | :--- |
| **Toy Prompt Wrapper** | Single prompt LLM CLI; takes issue text and writes code directly to disk. | Zero verification; high hallucination rate; produces syntax and runtime errors. | **Closed-loop Docker sandbox** running full pytest suite with zero code dispatched until 100% tests pass. |
| **Synthetic Benchmark Solver** | Tested only on static toy benchmarks or mock repositories. | Fails on real open source; doesn't handle complex dependencies or real GitHub APIs. | **Proven on live production open source** (`python-humanize #466` -> PR `#467` on GitHub). |
| **Monolithic LLM Dumper** | Sends entire 50,000-line repositories into prompt context. | Attention dilution, context limit exhaustion, high latency, hallucinated imports. | **Tree-sitter AST Slicing** extracting surgical 1,420 token subgraphs (85% token reduction). |
| **Unchecked Diff Generator** | Generates arbitrary code changes without security or style gates. | Path traversal (`../`), credential leaks, noisy whitespace churn. | **PatchValidator & DeterministicPatchCanonicalizer** enforcing strict security bounds. |
| **CLI-Only Script** | Terminal command line tool with no UI. | Poor judge experience; impossible to inspect telemetry or visual execution flow. | **Full-stack Next.js 14 Web Portal** with 60 FPS Three.js 3D state machine and live SSE telemetry. |

## 2. Competitive Differentiator Matrix

| Dimension | Standard Hackathon Agent | RepoMedic |
| :--- | :--- | :--- |
| **Core Model** | Generic external API | **NVIDIA Nemotron 3.5 Lightning (30B MoE)** via **NVIDIA NIM API** |
| **Verification Gate** | None (assumes code works) | **Zero-Hallucination Policy** (100% test pass in Docker) |
| **Context Extraction** | Naive keyword search | **Tree-sitter AST Slicing & Causal Program Slicing** |
| **Flakiness Defense** | None (flaky tests pass/fail randomly) | **DeepSWE Multi-Seed Shuffler** (seeds 42, 1337) |
| **Boundary Robustness** | Happy-path only | **Dynamic Contract Fuzzer** (None, numerics, unicode) |
| **Memory Safety** | None | **MemoryLeakGuard** (AST leak & recursion detection) |
| **Security Auditing** | None | **PatchValidator** (path traversal & secret exposure) |
| **External API Drift** | Fails when libraries update | **Tavily AI Search** autonomous drift self-healing |
| **User Experience** | Plain terminal output | **Next.js 14 + Three.js 3D WebGL Canvas + SSE** |
