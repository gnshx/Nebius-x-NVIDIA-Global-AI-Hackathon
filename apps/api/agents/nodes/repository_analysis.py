"""
RepoMedic — Node: REPOSITORY_ANALYSIS

Fetches the repository tree from GitHub via GitHubClient, summarizes its
structure, and identifies test/config files. Uses the fast model for the
summarisation step.

Enriches the `repository` state key and populates `repo_structure`,
`default_branch`, and `repo_snapshot_path`.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.orm import StepType
from services.github.client import github_client
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)

# File-path patterns that classify a file as a test or config file
_TEST_PATTERNS = ("test_", "_test.py", "/tests/", "/test/", "spec.py", "conftest.py")
_CONFIG_PATTERNS = (
    "requirements", "setup.py", "setup.cfg", "pyproject.toml",
    "Makefile", "tox.ini", ".github/", "Dockerfile", "docker-compose",
    ".env.example", "pytest.ini",
)


def _classify(path: str) -> str:
    """Return 'test', 'config', or 'source' for a repository path."""
    lower = path.lower()
    if any(p in lower for p in _TEST_PATTERNS):
        return "test"
    if any(p in lower for p in _CONFIG_PATTERNS):
        return "config"
    return "source"


async def run(state: RepoMedicState) -> dict:
    """Fetch repo tree, summarise structure, and enrich repository metadata."""
    installation_id: int = state["installation_id"]
    full_name: str = state["repository_full_name"]
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.fast.model

    logger.info("repository_analysis_start", run_id=run_id, repo=full_name)

    async with node_context(
        run_id,
        StepType.REPOSITORY_ANALYSIS,
        iteration,
        model_used,
        {"repo": full_name},
    ):
        # 1. Fetch fresh repository metadata (enriched)
        repo_meta = await github_client.get_repo(installation_id, full_name)
        default_branch: str = repo_meta.get("default_branch", "main")

        # 2. Fetch the full recursive tree for HEAD
        head_sha = await github_client.get_default_branch_sha(installation_id, full_name)
        tree_items = await github_client.get_repo_tree(installation_id, full_name, head_sha)

        # 3. Extract blob paths only (skip directories / submodules)
        all_paths: list[str] = [
            item["path"]
            for item in tree_items
            if item.get("type") == "blob"
        ]

        test_files = [p for p in all_paths if _classify(p) == "test"]
        config_files = [p for p in all_paths if _classify(p) == "config"]
        source_files = [p for p in all_paths if _classify(p) == "source"]

        logger.info(
            "repo_tree_fetched",
            run_id=run_id,
            total=len(all_paths),
            tests=len(test_files),
            configs=len(config_files),
            sources=len(source_files),
        )

        # 4. Build a compact structure summary and pass to fast model
        structure_sample = "\n".join(all_paths[:200])  # cap for context
        messages = [
            Message(
                role="user",
                content=(
                    f"Repository: {full_name}\n"
                    f"Language: {repo_meta.get('language', 'unknown')}\n"
                    f"Default branch: {default_branch}\n\n"
                    f"File tree (up to 200 paths):\n{structure_sample}\n\n"
                    "In 2-3 sentences: describe the repository structure, "
                    "primary language, test framework, and any notable conventions."
                ),
            )
        ]
        summary: str = await model_provider.fast.generate(messages)

        logger.info("repository_analysis_complete", run_id=run_id, summary=summary[:120])

    return {
        "repository": {
            **repo_meta,
            "structure_summary": summary,
            "test_files": test_files,
            "config_files": config_files,
        },
        "repo_structure": all_paths,
        "default_branch": default_branch,
    }
