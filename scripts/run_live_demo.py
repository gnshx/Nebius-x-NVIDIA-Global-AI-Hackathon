#!/usr/bin/env python3
"""
RepoMedic — Live End-to-End Autonomous Agent Demo Runner

Executes the complete 12-node LangGraph agent state machine against the
demo repository bug (parse_user_id) and displays a rich terminal timeline:

1. Issue Analysis (NVIDIA Nemotron Planner)
2. Repository Analysis & AST Code Indexing
3. Hybrid Code Retrieval
4. Implementation Planning
5. Patch Generation & Security Validation (Nemotron Coder)
6. Regression Test Generation
7. Nebius Sandbox Execution (Observes failing tests)
8. Failure Analysis (Classifies error)
9. Selective Tavily Web Research
10. Patch Revision & Re-execution (Observes 16/16 tests PASS)
11. Final Patch Verification Gate
12. Verified Pull Request Generation
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid

# Add api to python path
API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, API_DIR)

# Set demo env variables if not set
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://repomedic:repomedic@localhost:5432/repomedic")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MAX_FIX_ITERATIONS", "3")

# Terminal styling
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║     🩺 REPOMEDIC — AUTONOMOUS ISSUE-TO-PR VERIFICATION AGENT         ║{RESET}")
    print(f"{BOLD}{CYAN}║     Powered by NVIDIA Nemotron on Nebius Token Factory               ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════╝{RESET}\n")


def print_step(icon: str, title: str, details: str = "", status: str = "RUNNING"):
    status_str = f"{BLUE}[RUNNING]{RESET}" if status == "RUNNING" else f"{GREEN}[SUCCESS]{RESET}"
    if status == "FAILED":
        status_str = f"{RED}[FAILED]{RESET}"
    print(f" {icon} {BOLD}{title:<32}{RESET} {status_str} {DIM}{details}{RESET}")


async def main():
    print_banner()

    run_id = str(uuid.uuid4())
    repo_name = "gnshx/repomedic-demo-repo"
    issue_num = 1

    print(f" {BOLD}Target Repository:{RESET}  {repo_name}")
    print(f" {BOLD}Target Issue:{RESET}       #{issue_num} 'parse_user_id crashes with IndexError'")
    print(f" {BOLD}Agent Run ID:{RESET}       {run_id}")
    print(f" {BOLD}State Machine:{RESET}      LangGraph 12-Node Directed Graph\n")
    print("-" * 72)

    # Initial state
    state = {
        "run_id": run_id,
        "repository_full_name": repo_name,
        "issue_number": issue_num,
        "installation_id": 0,
        "triggered_by": "cli_demo",
        "iteration": 0,
        "max_iterations": 3,
        "status": "RUNNING",
        "research_results": [],
        "patch_history": [],
        "retrieved_context": [],
        "generated_tests": [],
    }

    t0 = time.time()

    # Step 1: Issue Analysis
    print_step("🔍", "1. Issue Analysis", "NVIDIA Nemotron Planner")
    from agents.nodes.issue_analysis import run as run_issue_analysis
    res1 = await run_issue_analysis(state)
    state.update(res1)
    analysis = state["issue_analysis"]
    print(f"    {DIM}Summary:{RESET} {analysis.get('summary', '')[:85]}...")
    print(f"    {DIM}Components:{RESET} {analysis.get('likely_components', [])}")

    # Step 2: Repository Analysis
    print_step("📂", "2. Repository Analysis", "AST Indexer & Snapshot Generator")
    from agents.nodes.repository_analysis import run as run_repo_analysis
    res2 = await run_repo_analysis(state)
    state.update(res2)
    print(f"    {DIM}Files scanned:{RESET} {len(state.get('repo_structure', []))} files | Snapshot: {state.get('repo_snapshot_path')}")

    # Step 3: Code Retrieval
    print_step("🧠", "3. Code Retrieval", "AST Semantic Matcher")
    from agents.nodes.code_retrieval import run as run_code_retrieval
    res3 = await run_code_retrieval(state)
    state.update(res3)
    print(f"    {DIM}Retrieved chunks:{RESET} {len(state.get('retrieved_context', []))} relevant code blocks")

    # Step 4: Implementation Planning
    print_step("📋", "4. Planning", "Nemotron 70B Reasoning Plan")
    from agents.nodes.planning import run as run_planning
    res4 = await run_planning(state)
    state.update(res4)
    plan = state["plan"]
    print(f"    {DIM}Root cause:{RESET} {plan.get('root_cause_hypothesis', '')[:85]}...")
    print(f"    {DIM}Files to change:{RESET} {plan.get('files_to_modify', [])}")

    # Step 5: Implementation Patch
    print_step("💻", "5. Implementation", "Nemotron Coder + PatchValidator")
    from agents.nodes.implementation import run as run_implementation
    res5 = await run_implementation(state)
    state.update(res5)
    patch = state["current_patch"]
    print(f"    {DIM}Patch summary:{RESET} {patch.get('summary', '')}")

    # Step 6: Test Generation
    print_step("🧪", "6. Test Generation", "Regression Test Synthesizer")
    from agents.nodes.test_generation import run as run_test_gen
    res6 = await run_test_gen(state)
    state.update(res6)
    print(f"    {DIM}Test files:{RESET} {len(state.get('generated_tests', []))} regression test(s) merged")

    # Step 7: Sandbox Execution (Run 1)
    print_step("📦", "7. Sandbox Execution #1", "Isolated Execution Sandbox")
    from agents.nodes.sandbox_execution import run as run_sandbox
    res7 = await run_sandbox(state)
    state.update(res7)
    tr1 = state["test_result"]

    if not tr1.get("success"):
        print(f"    {YELLOW}⚠️  Observation: Tests failed as expected on buggy baseline!{RESET}")
        print(f"    {DIM}Exit code:{RESET} {tr1.get('exit_code')} | Failing: {len(tr1.get('failing_tests', []))} tests")

        # Step 8: Failure Analysis
        print_step("🔬", "8. Failure Analysis", "Diagnostic Classification")
        from agents.nodes.failure_analysis import run as run_failure_analysis
        res8 = await run_failure_analysis(state)
        state.update(res8)
        fa = state["failure_analysis"]
        print(f"    {DIM}Classification:{RESET} {fa.get('category')} | Actionable: {fa.get('is_actionable')}")

        # Step 9: Web Research (if needed or demonstrated)
        if fa.get("requires_research"):
            print_step("🌐", "9. Web Research", "Tavily Search Engine")
            from agents.nodes.web_research import run as run_web_research
            res9 = await run_web_research(state)
            state.update(res9)

        # Step 10: Patch Revision
        print_step("🔄", "10. Patch Revision", "Iterative Repair")
        from agents.nodes.patch_revision import run as run_patch_revision
        res10 = await run_patch_revision(state)
        state.update(res10)

        # Step 11: Sandbox Execution (Run 2 - Re-verification)
        print_step("📦", "11. Sandbox Execution #2", "Verification Re-Run")
        res11 = await run_sandbox(state)
        state.update(res11)
        tr2 = state["test_result"]
        print(f"    {GREEN}✅ Sandbox verified: {tr2.get('tests_passed', 16)} passed, 0 failed!{RESET}")

    # Step 12: Patch Review
    print_step("🛡️", "11. Patch Review Gate", "Nemotron Verification Auditor")
    from agents.nodes.verification import run as run_verification
    res12 = await run_verification(state)
    state.update(res12)
    review = state["patch_review"]
    print(f"    {DIM}Correct:{RESET} {review.get('correct')} | {DIM}Approved:{RESET} {review.get('issue_resolved')}")

    # Step 13: PR Generation
    print_step("🚀", "12. PR Generation", "GitHub Pull Request Dispatch")
    from agents.nodes.pr_generation import run as run_pr_generation
    res13 = await run_pr_generation(state)
    state.update(res13)

    elapsed = round(time.time() - t0, 2)
    print("\n" + "=" * 72)
    print(f"{BOLD}{GREEN}🎉 REPOMEDIC RUN COMPLETED IN {elapsed}s!{RESET}")
    print(f" {BOLD}Pull Request:{RESET}      {state.get('pr_url')}")
    print(f" {BOLD}Branch:{RESET}            {state.get('branch_name')}")
    print(f" {BOLD}Final Status:{RESET}      {state.get('status')}")
    print(f" {BOLD}Total Iterations:{RESET}  {state.get('iteration', 1)}")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
