---
name: swe-bench-excellence
description: State-of-the-art methodology for Automated Program Repair (APR) and software engineering agents. Synthesizes principles from SWE-bench Verified leaderboard winners, test-time compute scaling, Tree-sitter causal slicing, and hermetic execution sandboxing.
---

# SWE-Bench Excellence & Automated Program Repair Playbook

This skill outlines the architectural requirements for building and evaluating production-grade coding agents capable of solving real-world GitHub issues.

## 1. Core Principles of SOTA APR Systems

1. **Hermetic Closed-Loop Execution:**
   - LLMs cannot reliably predict whether code executes cleanly without running the test suite.
   - Every candidate patch MUST be executed inside an isolated Docker container with the exact target virtual environment.
   - Code is NEVER dispatched or committed unless 100% of the repository's test suite passes.

2. **Causal AST Slicing vs. Context Flooding:**
   - Naive agents dump whole files or full repository trees into prompts (40k–128k tokens), causing severe attention dilution and high latency.
   - SOTA agents use Tree-sitter AST parsing to trace caller-callee dependency chains, extracting surgical 1,000–2,000 token subgraphs that capture exact semantic context.

3. **Multi-Seed Flakiness Mitigation (DeepSWE Pattern):**
   - In real-world test suites, test ordering and environmental race conditions produce false passes.
   - SOTA systems run tests under randomized seed shuffles (e.g., seeds 42 and 1337) to guarantee patch stability.

4. **Dynamic Contract Fuzzing:**
   - LLM patches frequently solve the reported bug while breaking adjacent contracts (e.g. passing `None`, negative integers, or UTF-8 strings).
   - Dynamic fuzzing evaluates edge conditions at function boundaries before candidate finalization.

5. **Memory Leak & Infinite Recursion Guards:**
   - Static AST inspection verifies that modified loops, recursion paths, and persistent caching do not introduce unbounded memory growth.

## 2. Benchmark Scorecard

| Dimension | Naive Coding Agent | SOTA SWE-Bench Champion (RepoMedic) |
| :--- | :--- | :--- |
| **Context Strategy** | Full-file grep | Tree-sitter Causal AST Slicing (1,420 tokens) |
| **Execution Sandbox** | Host shell / none | Docker isolated container sandbox |
| **Oracle Strategy** | LLM self-evaluation | Pytest Oracle + Multi-Seed Shuffler |
| **Hallucination Defense** | None | Zero-Hallucination Policy (100% pass required) |
| **Security Auditing** | None | PatchValidator (path traversal, secret leak checks) |
| **Real Open-Source Proof**| Synthetic mocks | Real GitHub Issue (`humanize #466` -> PR `#467`) |
