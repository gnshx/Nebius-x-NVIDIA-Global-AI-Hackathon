"""
RepoMedic — LangGraph State Machine Graph

Defines the complete agent execution graph with:
- 12 nodes (one per agent step type)
- Conditional routing for retry loop and research branch
- Iteration cap enforcement (MAX_FIX_ITERATIONS)
- DB persistence and SSE event emission at each node
"""

from __future__ import annotations

import structlog
from langgraph.graph import END, StateGraph

from agents.state import RepoMedicState
from agents.nodes import (
    issue_analysis,
    repository_analysis,
    code_retrieval,
    planning,
    implementation,
    test_generation,
    sandbox_execution,
    failure_analysis,
    web_research,
    patch_revision,
    verification,
    pr_generation,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Conditional routing functions
# ---------------------------------------------------------------------------

def route_after_sandbox(state: RepoMedicState) -> str:
    """
    After sandbox execution:
    - tests passed → verification
    - tests failed + iterations remaining → failure_analysis
    - tests failed + max iterations hit → END (FAILED)
    """
    test_result = state.get("test_result")
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 3)

    if test_result and test_result.get("success"):
        logger.info("routing_to_verification", run_id=state.get("run_id"))
        return "verification"

    if iteration >= max_iter:
        logger.warning(
            "max_iterations_reached",
            run_id=state.get("run_id"),
            iteration=iteration,
            max_iterations=max_iter,
        )
        return "end_failed"

    logger.info(
        "routing_to_failure_analysis",
        run_id=state.get("run_id"),
        iteration=iteration,
    )
    return "failure_analysis"


def route_after_failure(state: RepoMedicState) -> str:
    """
    After failure analysis:
    - requires_research=True → web_research
    - otherwise → patch_revision
    """
    fa = state.get("failure_analysis") or {}
    if fa.get("requires_research") and fa.get("research_query"):
        logger.info("routing_to_web_research", query=fa.get("research_query"))
        return "web_research"
    return "patch_revision"


def route_after_verification(state: RepoMedicState) -> str:
    """
    After patch review:
    - review approved → pr_generation
    - review rejected → END (FAILED, no PR)
    """
    review = state.get("patch_review") or {}
    if review.get("correct") and review.get("issue_resolved"):
        return "pr_generation"
    logger.warning(
        "patch_review_rejected",
        run_id=state.get("run_id"),
        summary=review.get("summary"),
    )
    return "end_failed"


async def node_end_failed(state: RepoMedicState) -> dict:
    """Terminal failure node — marks run as FAILED."""
    from agents.nodes.base import emit_event, update_run_status
    await update_run_status(state["run_id"], "FAILED")
    await emit_event(state["run_id"], "run_failed", {
        "iteration": state.get("iteration"),
        "error": state.get("error"),
    })
    return {"status": "FAILED"}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Build and compile the RepoMedic LangGraph state machine."""
    graph = StateGraph(RepoMedicState)

    # ── Add nodes ───────────────────────────────────────────────────────────
    graph.add_node("issue_analysis", issue_analysis.run)
    graph.add_node("repository_analysis", repository_analysis.run)
    graph.add_node("code_retrieval", code_retrieval.run)
    graph.add_node("planning", planning.run)
    graph.add_node("implementation", implementation.run)
    graph.add_node("test_generation", test_generation.run)
    graph.add_node("sandbox_execution", sandbox_execution.run)
    graph.add_node("failure_analysis", failure_analysis.run)
    graph.add_node("web_research", web_research.run)
    graph.add_node("patch_revision", patch_revision.run)
    graph.add_node("verification", verification.run)
    graph.add_node("pr_generation", pr_generation.run)
    graph.add_node("end_failed", node_end_failed)

    # ── Entry point ──────────────────────────────────────────────────────────
    graph.set_entry_point("issue_analysis")

    # ── Linear edges ────────────────────────────────────────────────────────
    graph.add_edge("issue_analysis", "repository_analysis")
    graph.add_edge("repository_analysis", "code_retrieval")
    graph.add_edge("code_retrieval", "planning")
    graph.add_edge("planning", "implementation")
    graph.add_edge("implementation", "test_generation")
    graph.add_edge("test_generation", "sandbox_execution")

    # ── Conditional: after sandbox ────────────────────────────────────────────
    graph.add_conditional_edges(
        "sandbox_execution",
        route_after_sandbox,
        {
            "verification": "verification",
            "failure_analysis": "failure_analysis",
            "end_failed": "end_failed",
        },
    )

    # ── Conditional: after failure analysis ──────────────────────────────────
    graph.add_conditional_edges(
        "failure_analysis",
        route_after_failure,
        {
            "web_research": "web_research",
            "patch_revision": "patch_revision",
        },
    )

    # web_research always → patch_revision
    graph.add_edge("web_research", "patch_revision")

    # patch_revision → sandbox_execution (retry loop)
    graph.add_edge("patch_revision", "sandbox_execution")

    # ── Conditional: after verification ─────────────────────────────────────
    graph.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "pr_generation": "pr_generation",
            "end_failed": "end_failed",
        },
    )

    # ── Terminal edges ───────────────────────────────────────────────────────
    graph.add_edge("pr_generation", END)
    graph.add_edge("end_failed", END)

    return graph.compile()


# Singleton compiled graph
repomedic_graph = build_graph()
