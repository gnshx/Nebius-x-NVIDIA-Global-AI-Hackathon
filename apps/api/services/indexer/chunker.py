"""
RepoMedic — AST Code Chunker & Symbol Indexer

Parses Python source files using Python AST (with tree-sitter compatibility)
to extract:
- Functions (name, args, docstring, lines, body)
- Classes and methods
- Module-level docstrings and imports
- Call relationships and symbols

Stores structured metadata matching the CodeChunk schema for pgvector indexing.
"""

from __future__ import annotations

import ast
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class CodeSymbolChunk:
    symbol: str
    chunk_type: str  # function | class | method | module | imports
    start_line: int
    end_line: int
    content: str
    docstring: str | None
    imports: list[str]
    metadata: dict[str, Any]


class PythonASTChunker:
    """Extract semantic code chunks and symbols from Python source files."""

    def __init__(self, max_chunk_lines: int = 150) -> None:
        self.max_chunk_lines = max_chunk_lines

    def chunk_file(self, file_path: str, code: str) -> list[CodeSymbolChunk]:
        """Parse source code into semantic chunks."""
        chunks: list[CodeSymbolChunk] = []
        lines = code.splitlines(keepends=True)
        total_lines = len(lines)

        try:
            tree = ast.parse(code, filename=file_path)
        except SyntaxError:
            # Fall back to whole-file or windowed chunking for syntax errors
            return self._fallback_window_chunk(file_path, code, lines)

        # 1. Extract module-level imports
        imports = self._extract_imports(tree)
        if imports:
            import_lines = [
                lines[node.lineno - 1]
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom)) and hasattr(node, "lineno")
            ]
            if import_lines:
                chunks.append(
                    CodeSymbolChunk(
                        symbol="<imports>",
                        chunk_type="imports",
                        start_line=1,
                        end_line=min(30, total_lines),
                        content="".join(import_lines).strip(),
                        docstring=None,
                        imports=imports,
                        metadata={"file_path": file_path, "import_count": len(imports)},
                    )
                )

        # 2. Extract module docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            chunks.append(
                CodeSymbolChunk(
                    symbol="<module_doc>",
                    chunk_type="module",
                    start_line=1,
                    end_line=min(20, total_lines),
                    content=module_doc,
                    docstring=module_doc,
                    imports=imports,
                    metadata={"file_path": file_path},
                )
            )

        # 3. Extract top-level functions and classes
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunks.append(self._chunk_function(node, lines, file_path, imports))
            elif isinstance(node, ast.ClassDef):
                chunks.append(self._chunk_class(node, lines, file_path, imports))
                # Also index individual class methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        chunks.append(
                            self._chunk_function(
                                item,
                                lines,
                                file_path,
                                imports,
                                parent_class=node.name,
                            )
                        )

        # If file had no functions/classes (e.g. config or script), chunk whole file
        if not chunks and code.strip():
            chunks.append(
                CodeSymbolChunk(
                    symbol="<file>",
                    chunk_type="module",
                    start_line=1,
                    end_line=total_lines,
                    content=code.strip(),
                    docstring=module_doc,
                    imports=imports,
                    metadata={"file_path": file_path},
                )
            )

        return chunks

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports

    def _chunk_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: list[str],
        file_path: str,
        imports: list[str],
        parent_class: str | None = None,
    ) -> CodeSymbolChunk:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line + len(node.body))
        content = "".join(lines[start_line - 1 : end_line]).strip()
        docstring = ast.get_docstring(node)

        symbol_name = f"{parent_class}.{node.name}" if parent_class else node.name
        chunk_type = "method" if parent_class else "function"

        # Extract arg names
        args = [arg.arg for arg in node.args.args]

        return CodeSymbolChunk(
            symbol=symbol_name,
            chunk_type=chunk_type,
            start_line=start_line,
            end_line=end_line,
            content=content,
            docstring=docstring,
            imports=imports,
            metadata={
                "file_path": file_path,
                "args": args,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "parent_class": parent_class,
            },
        )

    def _chunk_class(
        self,
        node: ast.ClassDef,
        lines: list[str],
        file_path: str,
        imports: list[str],
    ) -> CodeSymbolChunk:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line + 20)
        # For class header, capture class def plus docstring and method signatures
        header_lines = lines[start_line - 1 : min(start_line + 15, len(lines))]
        content = "".join(header_lines).strip()
        docstring = ast.get_docstring(node)

        methods = [
            m.name
            for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        return CodeSymbolChunk(
            symbol=node.name,
            chunk_type="class",
            start_line=start_line,
            end_line=end_line,
            content=content,
            docstring=docstring,
            imports=imports,
            metadata={
                "file_path": file_path,
                "methods": methods,
            },
        )

    def _fallback_window_chunk(
        self, file_path: str, code: str, lines: list[str]
    ) -> list[CodeSymbolChunk]:
        """Simple line-window fallback for non-parsable or large scripts."""
        chunks = []
        window = 60
        for i in range(0, len(lines), window):
            chunk_lines = lines[i : i + window]
            chunks.append(
                CodeSymbolChunk(
                    symbol=f"lines_{i+1}_{i+len(chunk_lines)}",
                    chunk_type="block",
                    start_line=i + 1,
                    end_line=i + len(chunk_lines),
                    content="".join(chunk_lines).strip(),
                    docstring=None,
                    imports=[],
                    metadata={"file_path": file_path},
                )
            )
        return chunks


python_ast_chunker = PythonASTChunker()
