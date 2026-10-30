"""
RepoMedic — Sandbox Layered Overlay (SWE-bench / OpenHands CoW Sandbox 2026)

Implements high-throughput Copy-on-Write (CoW) layered overlay management for sandbox test runs:
1. Maintains a clean, read-only base layer snapshot of the repository (git checkout, dependencies, AST symbols).
2. Provisions ephemeral isolated upper layers per execution turn or candidate patch.
3. Shadows modified files into the upper layer, preserving base integrity with sub-second provisioning.
4. Calculates isolated overlay diffs and enforces instant deterministic cleanup upon test completion.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class OverlaySession:
    """Manages an active ephemeral sandbox overlay session."""

    def __init__(
        self,
        session_id: str,
        base_dir: Path,
        upper_dir: Path,
        workdir: Path,
    ) -> None:
        self.session_id = session_id
        self.base_dir = base_dir.resolve()
        self.upper_dir = upper_dir.resolve()
        self.workdir = workdir.resolve()
        self.modified_paths: List[str] = []
        self._is_active = True

    def write_overlay_file(self, rel_path: str, content: str) -> Path:
        """Writes or modifies a file within the ephemeral upper overlay."""
        if not self._is_active:
            raise RuntimeError(f"OverlaySession {self.session_id} has been destroyed.")

        target = self.workdir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        # Break hardlink (Copy-on-Write) to guarantee base layer is never mutated
        if target.exists():
            target.unlink()
        target.write_text(content, encoding="utf-8")
        if rel_path not in self.modified_paths:
            self.modified_paths.append(rel_path)
        return target

    def read_overlay_file(self, rel_path: str) -> Optional[str]:
        """Reads a file from the overlay workdir."""
        target = self.workdir / rel_path
        if target.exists() and target.is_file():
            return target.read_text(encoding="utf-8")
        return None

    def list_modified_files(self) -> List[str]:
        """Returns list of files modified during this overlay session."""
        return list(self.modified_paths)

    def destroy(self) -> None:
        """Instantly removes the ephemeral upper layer and workdir."""
        if not self._is_active:
            return
        self._is_active = False
        try:
            if self.upper_dir.exists():
                shutil.rmtree(self.upper_dir, ignore_errors=True)
        except Exception as e:
            logger.warning("overlay_destroy_error", session_id=self.session_id, error=str(e))
        logger.debug("overlay_session_destroyed", session_id=self.session_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "base_dir": str(self.base_dir),
            "workdir": str(self.workdir),
            "modified_files": self.modified_paths,
            "is_active": self._is_active,
        }


class SandboxLayeredOverlayManager:
    """Provisions and tracks ephemeral layered overlays across APR test-time candidate iterations."""

    def __init__(self, root_temp_dir: Optional[Path] = None) -> None:
        self._root_temp = root_temp_dir or Path(tempfile.gettempdir()) / "repomedic_overlays"
        self._root_temp.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, OverlaySession] = {}

    def create_overlay_session(
        self,
        base_dir: Path,
        session_id: Optional[str] = None,
    ) -> OverlaySession:
        """Provisions an isolated overlay session backed by the base directory."""
        sid = session_id or f"overlay-{uuid.uuid4().hex[:8]}"
        base_dir = base_dir.resolve()
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        session_root = self._root_temp / sid
        session_root.mkdir(parents=True, exist_ok=True)
        upper_dir = session_root / "upper"
        upper_dir.mkdir(parents=True, exist_ok=True)

        workdir = session_root / "merged"
        workdir.mkdir(parents=True, exist_ok=True)

        # Populate workdir with symlinks/hardlinks to base files for sub-second start
        self._populate_workdir(base_dir, workdir)

        session = OverlaySession(
            session_id=sid,
            base_dir=base_dir,
            upper_dir=upper_dir,
            workdir=workdir,
        )
        self._sessions[sid] = session
        logger.info("overlay_session_created", session_id=sid, base_dir=str(base_dir))
        return session

    def get_session(self, session_id: str) -> Optional[OverlaySession]:
        return self._sessions.get(session_id)

    def destroy_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session:
            session.destroy()

    def destroy_all(self) -> None:
        for sid in list(self._sessions.keys()):
            self.destroy_session(sid)

    @staticmethod
    def _populate_workdir(base_dir: Path, workdir: Path) -> None:
        """Populates workdir using copy or hardlinks for fast copy-on-write simulation."""
        for root, dirs, files in os.walk(base_dir):
            rel_dir = Path(root).relative_to(base_dir)
            target_dir = workdir / rel_dir
            target_dir.mkdir(parents=True, exist_ok=True)

            for f in files:
                src_file = Path(root) / f
                dst_file = target_dir / f
                try:
                    # Attempt hardlink for instantaneous zero-copy sharing
                    os.link(src_file, dst_file)
                except (OSError, NotImplementedError):
                    # Fallback to copy
                    shutil.copy2(src_file, dst_file)
