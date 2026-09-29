"""
RepoMedic — Node: CODE_RETRIEVAL

Retrieves the most relevant code chunks from pgvector for the current issue.

Strategy:
1. Embed the combined issue text using the fast model.
2. Query `code_chunks` via cosine distance (<->) for the repository, LIMIT 20.
3. Also pull any files explicitly named in `issue_analysis.relevant_files`.
4. Deduplicate by chunk id.
5. Cap total content at `settings.max_context_tokens` (rough word-count proxy).
"""

from __future__ import annotations

import structlog
from sqlalchemy import select, text

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from config import settings
from db.database import AsyncSessionLocal
from models.orm import CodeChunk, Repository, StepType
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)

_VECTOR_LIMIT = 20
_EXPLICIT_FILE_LIMIT = 5  # extra files from relevant_files list


async def run(state: RepoMedicState) -> dict:
    """Retrieve relevant code chunks from pgvector for the current issue."""
    issue = state["issue"]
    issue_analysis = state.get("issue_analysis") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.fast.model
    full_name: str = state["repository_full_name"]

    likely_components: list[str] = issue_analysis.get("likely_components", [])
    relevant_files: list[str] = issue_analysis.get("relevant_files", [])

    # Build the composite search query text
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

    async with node_context(
        run_id,
        StepType.CODE_RETRIEVAL,
        iteration,
        model_used,
        {"likely_components": likely_components, "relevant_files": relevant_files},
    ):
        # 1. Embed the query
        embedding: list[float] = await model_provider.fast.embed(query_text)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        chunks: list[dict] = []
        seen_ids: set[str] = set()

        async with AsyncSessionLocal() as session:
            # Resolve repository DB id
            repo_row = await session.execute(
                select(Repository).where(Repository.full_name == full_name)
            )
            repo_obj = repo_row.scalar_one_or_none()
            if repo_obj is None:
                logger.warning("code_retrieval_no_repo", run_id=run_id, repo=full_name)
                return {"retrieved_context": []}

            repo_id = str(repo_obj.id)

            # 2. Vector similarity search
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
                {"repo_id": repo_id, "embedding": embedding_str, "limit": _VECTOR_LIMIT},
            )
            for row in result.mappings():
                chunk_id = str(row["id"])
                if chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    chunks.append(dict(row))

            # 3. Pull explicitly mentioned files
            if relevant_files:
                for file_path in relevant_files[:_EXPLICIT_FILE_LIMIT]:
                    file_result = await session.execute(
                        select(CodeChunk)
                        .where(
                            CodeChunk.repository_id == repo_obj.id,
                            CodeChunk.path == file_path,
                        )
                        .limit(10)
                    )
                    for chunk_obj in file_result.scalars():
                        chunk_id = str(chunk_obj.id)
                        if chunk_id not in seen_ids:
                            seen_ids.add(chunk_id)
                            chunks.append({
                                "id": chunk_id,
                                "path": chunk_obj.path,
                                "language": chunk_obj.language,
                                "chunk_type": chunk_obj.chunk_type,
                                "symbol": chunk_obj.symbol,
                                "content": chunk_obj.content,
                                "start_line": chunk_obj.start_line,
                                "end_line": chunk_obj.end_line,
                                "imports": chunk_obj.imports,
                                "docstring": chunk_obj.docstring,
                            })

        # 4. Cap total word count to max_context_tokens (rough proxy)
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
