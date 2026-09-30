"""
RepoMedic — Node: REPOSITORY_ANALYSIS

Fetches the repository tree, creates a repo snapshot tarball for sandbox execution,
runs the AST chunker to index functions/classes/imports, and generates a structural summary.
"""

from __future__ import annotations

import io
import os
import tarfile
import tempfile
from pathlib import Path

import structlog
from sqlalchemy import select

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from db.database import AsyncSessionLocal
from models.orm import CodeChunk, Repository
from models.enums import StepType
from services.github.client import github_client
from services.indexer.chunker import python_ast_chunker
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)

_TEST_PATTERNS = ("test_", "_test.py", "/tests/", "/test/", "spec.py", "conftest.py")
_CONFIG_PATTERNS = (
    "requirements", "setup.py", "setup.cfg", "pyproject.toml",
    "Makefile", "tox.ini", ".github/", "Dockerfile", "docker-compose",
    ".env.example", "pytest.ini",
)


def _classify(path: str) -> str:
    lower = path.lower()
    if any(p in lower for p in _TEST_PATTERNS):
        return "test"
    if any(p in lower for p in _CONFIG_PATTERNS):
        return "config"
    return "source"


def _create_local_snapshot(target_dir: Path) -> str:
    """Create a tarball snapshot from a local directory (e.g. demo repo)."""
    tmp_tar = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    with tarfile.open(tmp_tar.name, "w:gz") as tar:
        for root, _, files in os.walk(target_dir):
            if any(ign in root for ign in [".git", "__pycache__", ".pytest_cache", ".venv"]):
                continue
            for f in files:
                full_path = Path(root) / f
                arcname = full_path.relative_to(target_dir)
                tar.add(full_path, arcname=str(arcname))
    return tmp_tar.name


async def run(state: RepoMedicState) -> dict:
    """Fetch repo tree, index code symbols, create snapshot, and summarise structure."""
    installation_id: int = state.get("installation_id", 0)
    full_name: str = state["repository_full_name"]
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.fast.model

    logger.info("repository_analysis_start", run_id=run_id, repo=full_name)

    repo_meta = state.get("repository") or {}
    default_branch = state.get("default_branch") or "main"
    all_paths: list[str] = []
    file_contents: dict[str, str] = {}
    snapshot_path: str | None = None

    async with node_context(
        run_id,
        StepType.REPOSITORY_ANALYSIS,
        iteration,
        model_used,
        {"repo": full_name},
    ):
        # 1. Check if analyzing the local demo repository
        is_demo = "demo" in full_name.lower() or not installation_id
        demo_dir = Path("demo")

        if is_demo and demo_dir.exists():
            for p in demo_dir.rglob("*"):
                if p.is_file() and not any(ign in str(p) for ign in [".git", "__pycache__", ".pytest_cache"]):
                    rel_p = str(p.relative_to(demo_dir))
                    all_paths.append(rel_p)
                    if p.suffix == ".py" or p.name in ["pyproject.toml", "requirements.txt"]:
                        try:
                            file_contents[rel_p] = p.read_text(encoding="utf-8")
                        except Exception:
                            pass
            snapshot_path = _create_local_snapshot(demo_dir)
            repo_meta["name"] = "demo-utils"
            repo_meta["language"] = "Python"
        else:
            try:
                fetched_meta = await github_client.get_repo(installation_id, full_name)
                repo_meta.update(fetched_meta)
                default_branch = repo_meta.get("default_branch", "main")
                head_sha = await github_client.get_default_branch_sha(installation_id, full_name)
                tree_items = await github_client.get_repo_tree(installation_id, full_name, head_sha)
                all_paths = [item["path"] for item in tree_items if item.get("type") == "blob"]

                # Fetch key code files for indexing (capped to top 25 python files)
                py_files = [p for p in all_paths if p.endswith(".py")][:25]
                for p in py_files:
                    try:
                        content = await github_client.get_file_content(installation_id, full_name, p, head_sha)
                        file_contents[p] = content
                    except Exception:
                        pass
            except Exception as e:
                logger.warning("github_tree_fetch_failed", error=str(e))
                if demo_dir.exists():
                    snapshot_path = _create_local_snapshot(demo_dir)

        test_files = [p for p in all_paths if _classify(p) == "test"]
        config_files = [p for p in all_paths if _classify(p) == "config"]
        source_files = [p for p in all_paths if _classify(p) == "source"]

        # 2. AST Chunking across collected files
        parsed_chunks: list[dict] = []
        for file_path, code in file_contents.items():
            if file_path.endswith(".py"):
                symbol_chunks = python_ast_chunker.chunk_file(file_path, code)
                for sc in symbol_chunks:
                    parsed_chunks.append({
                        "path": file_path,
                        "symbol": sc.symbol,
                        "chunk_type": sc.chunk_type,
                        "start_line": sc.start_line,
                        "end_line": sc.end_line,
                        "content": sc.content,
                        "docstring": sc.docstring,
                        "imports": sc.imports,
                        "language": "python",
                    })

        # 3. Persist chunks to pgvector / database if available
        try:
            async with AsyncSessionLocal() as session:
                repo_row = await session.execute(
                    select(Repository).where(Repository.full_name == full_name)
                )
                repo_obj = repo_row.scalar_one_or_none()
                if repo_obj:
                    for chunk in parsed_chunks[:50]:
                        embedding = None
                        try:
                            embedding = await model_provider.fast.embed(chunk["content"][:1000])
                        except Exception:
                            pass
                        db_chunk = CodeChunk(
                            repository_id=repo_obj.id,
                            path=chunk["path"],
                            language=chunk["language"],
                            chunk_type=chunk["chunk_type"],
                            symbol=chunk["symbol"],
                            content=chunk["content"],
                            start_line=chunk["start_line"],
                            end_line=chunk["end_line"],
                            imports=chunk["imports"],
                            docstring=chunk["docstring"],
                            embedding=embedding,
                        )
                        session.add(db_chunk)
                    await session.commit()
        except Exception as db_exc:
            logger.warning("chunk_db_persist_skipped", error=str(db_exc))

        # 4. Fast model summary of repo structure
        structure_sample = "\n".join(all_paths[:150])
        messages = [
            Message(
                role="user",
                content=(
                    f"Repository: {full_name}\n"
                    f"Language: {repo_meta.get('language', 'Python')}\n"
                    f"Files:\n{structure_sample}\n\n"
                    "In 2 sentences: summarize what this repo does, its structure, and test conventions."
                ),
            )
        ]
        try:
            summary = await model_provider.fast.generate(messages)
        except Exception:
            summary = f"Python repository '{full_name}' with {len(all_paths)} files and pytest test suite."

    return {
        "repository": {
            **repo_meta,
            "structure_summary": summary,
            "test_files": test_files,
            "config_files": config_files,
        },
        "repo_structure": all_paths,
        "default_branch": default_branch,
        "repo_snapshot_path": snapshot_path,
        "indexed_chunks": parsed_chunks,
    }
