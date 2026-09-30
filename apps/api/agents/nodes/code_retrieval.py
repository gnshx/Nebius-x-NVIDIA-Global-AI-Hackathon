"""
RepoMedic — Node: CODE_RETRIEVAL

Retrieves the most relevant code chunks from pgvector, enriched with AST-indexed
chunks and direct file lookups so that the planner model is NEVER starved of context.
"""

from __future__ import annotations

from pathlib import Path
import structlog
from sqlalchemy import select, text

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from config import settings
from db.database import AsyncSessionLocal
from models.orm import CodeChunk, Repository
from models.enums import StepType
from services.nebius.client import model_provider

logger = structlog.get_logger(__name__)

_VECTOR_LIMIT = 20
_EXPLICIT_FILE_LIMIT = 5


async def run(state: RepoMedicState) -> dict:
    """Retrieve relevant code chunks for the bug report."""
    issue = state.get("issue") or {}
    issue_analysis = state.get("issue_analysis") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.fast.model
    full_name: str = state["repository_full_name"]
    indexed_chunks = state.get("indexed_chunks") or []

    likely_components: list[str] = issue_analysis.get("likely_components", [])
    relevant_files: list[str] = issue_analysis.get("relevant_files", [])

    query_text = "\n".join(
        filter(None, [
            issue.get("title", ""),
            issue.get("body", "") or "",
            " ".join(likely_components),
        ])
    )

    logger.info(
        "code_retrieval_start",
        run_id=run_id,
        repo=full_name,
        components=likely_components,
        relevant_files=relevant_files,
    )

    chunks: list[dict] = []
    seen_ids: set[str] = set()

    async with node_context(
        run_id,
        StepType.CODE_RETRIEVAL,
        iteration,
        model_used,
        {"likely_components": likely_components, "relevant_files": relevant_files},
    ):
        # 1. Try vector similarity search from PostgreSQL / pgvector
        try:
            embedding: list[float] = await model_provider.fast.embed(query_text)
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

            async with AsyncSessionLocal() as session:
                repo_row = await session.execute(
                    select(Repository).where(Repository.full_name == full_name)
                )
                repo_obj = repo_row.scalar_one_or_none()
                if repo_obj:
                    vector_sql = text(
                        "SELECT id, path, language, chunk_type, symbol, content, "
                        "       start_line, end_line, imports, docstring "
                        "FROM code_chunks "
                        "WHERE repository_id = :repo_id "
                        "ORDER BY embedding <-> CAST(:embedding AS vector) "
                        "LIMIT :limit"
                    )
                    result = await session.execute(
                        vector_sql,
                        {"repo_id": str(repo_obj.id), "embedding": embedding_str, "limit": _VECTOR_LIMIT},
                    )
                    for row in result.mappings():
                        cid = f"{row['path']}:{row['start_line']}"
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            chunks.append(dict(row))
        except Exception as v_exc:
            logger.debug("vector_retrieval_fallback", error=str(v_exc))

        # 2. Enrich from AST chunks in state (keyword + component matching)
        if indexed_chunks:
            keywords = set(w.lower() for w in query_text.replace("\n", " ").split() if len(w) > 3)
            scored_chunks = []
            for ic in indexed_chunks:
                score = 0
                path_lower = ic["path"].lower()
                sym_lower = (ic["symbol"] or "").lower()
                content_lower = ic["content"].lower()

                # Prioritize files in relevant_files or likely_components
                if any(rf.lower() in path_lower for rf in relevant_files):
                    score += 15
                if any(lc.lower() in sym_lower or lc.lower() in path_lower for lc in likely_components):
                    score += 10
                for kw in keywords:
                    if kw in sym_lower:
                        score += 5
                    elif kw in content_lower:
                        score += 1

                scored_chunks.append((score, ic))

            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            for _, sc in scored_chunks[:12]:
                cid = f"{sc['path']}:{sc.get('start_line', 0)}"
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    chunks.append(sc)

        # 3. Direct local disk fallback for demo / test environments
        if not chunks:
            for cand in ["demo/src/utils.py", "demo/tests/test_utils.py", "src/utils.py", "tests/test_utils.py"]:
                p = Path(cand)
                if p.exists():
                    chunks.append({
                        "path": str(p),
                        "symbol": "<module>",
                        "chunk_type": "file",
                        "content": p.read_text(encoding="utf-8")[:4000],
                        "start_line": 1,
                        "end_line": 100,
                        "imports": [],
                        "docstring": "",
                    })

        # 4. Cap total word count to settings.max_context_tokens
        capped_chunks: list[dict] = []
        word_count = 0
        for chunk in chunks:
            content = chunk.get("content", "")
            words = len(content.split())
            if word_count + words > settings.max_context_tokens:
                break
            capped_chunks.append(chunk)
            word_count += words

    logger.info(
        "code_retrieval_complete",
        run_id=run_id,
        total_retrieved=len(chunks),
        after_cap=len(capped_chunks),
        approx_words=word_count,
    )

    return {"retrieved_context": capped_chunks}
