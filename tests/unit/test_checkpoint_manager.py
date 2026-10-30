"""
Unit tests for WorkspaceCheckpointManager (SWE-Search / MCTS Rollback).
"""

import tempfile
from pathlib import Path
import pytest
from services.checkpoint_manager import WorkspaceCheckpointManager


def test_create_and_restore_checkpoint():
    with tempfile.TemporaryDirectory() as tmp_workdir, tempfile.TemporaryDirectory() as tmp_storage:
        workdir = Path(tmp_workdir)
        storage = Path(tmp_storage)

        # 1. Create initial files
        file1 = workdir / "main.py"
        file1.write_text("def hello(): return 'world'")

        sub_dir = workdir / "src"
        sub_dir.mkdir()
        file2 = sub_dir / "utils.py"
        file2.write_text("x = 10")

        mgr = WorkspaceCheckpointManager(storage_dir=storage)
        meta = mgr.create_checkpoint(workdir, "baseline")

        assert meta.name == "baseline"
        assert meta.files_count == 2
        assert mgr.has_checkpoint("baseline")

        # 2. Simulate dirty modification / failed patch
        file1.write_text("def broken(): syntax error")
        dirty_file = workdir / "dirty_artifact.tmp"
        dirty_file.write_text("junk")

        assert "broken" in file1.read_text()
        assert dirty_file.exists()

        # 3. Rollback to baseline checkpoint
        restored = mgr.restore_checkpoint(workdir, "baseline")
        assert restored is True

        # 4. Verify original state is restored cleanly
        assert file1.read_text() == "def hello(): return 'world'"
        assert not dirty_file.exists()
        assert file2.read_text() == "x = 10"


def test_restore_nonexistent_checkpoint():
    with tempfile.TemporaryDirectory() as tmp_workdir:
        mgr = WorkspaceCheckpointManager()
        restored = mgr.restore_checkpoint(Path(tmp_workdir), "nonexistent")
        assert restored is False


def test_checkpoint_clear():
    with tempfile.TemporaryDirectory() as tmp_workdir, tempfile.TemporaryDirectory() as tmp_storage:
        workdir = Path(tmp_workdir)
        (workdir / "f.txt").write_text("test")

        mgr = WorkspaceCheckpointManager(storage_dir=Path(tmp_storage))
        mgr.create_checkpoint(workdir, "test_cp")
        assert mgr.has_checkpoint("test_cp")

        mgr.clear()
        assert not mgr.has_checkpoint("test_cp")
