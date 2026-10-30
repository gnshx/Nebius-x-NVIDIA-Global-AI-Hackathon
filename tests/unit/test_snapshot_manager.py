"""Unit tests for RepoMedic's SandboxSnapshotManager service."""

import tempfile
from pathlib import Path
from services.snapshot_manager import SandboxSnapshotManager


def test_dependency_fingerprint_generation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '0.1.0'", encoding="utf-8")
        (tmp_path / "requirements.txt").write_text("pytest>=8.0.0\nstructlog>=24.1.0", encoding="utf-8")

        fp1 = SandboxSnapshotManager.compute_dependency_fingerprint(tmp_path)
        assert len(fp1) == 16

        # Modifying a dependency file changes fingerprint
        (tmp_path / "requirements.txt").write_text("pytest>=8.0.0\nstructlog>=24.1.0\nrequests>=2.31.0", encoding="utf-8")
        fp2 = SandboxSnapshotManager.compute_dependency_fingerprint(tmp_path)
        assert fp1 != fp2


def test_cache_key_generation():
    key1 = SandboxSnapshotManager.compute_cache_key("repo-a", "abc12345")
    key2 = SandboxSnapshotManager.compute_cache_key("repo-a", "abc12345")
    key3 = SandboxSnapshotManager.compute_cache_key("repo-b", "abc12345")

    assert key1 == key2
    assert key1 != key3
    assert len(key1) == 24


def test_snapshot_save_and_restore():
    with tempfile.TemporaryDirectory() as cache_dir, tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dst_dir:
        cache_path = Path(cache_dir)
        src_path = Path(src_dir)
        dst_path = Path(dst_dir)

        # Populate source directory
        (src_path / "main.py").write_text("print('hello world')", encoding="utf-8")
        (src_path / "sub").mkdir()
        (src_path / "sub" / "lib.py").write_text("X = 42", encoding="utf-8")

        mgr = SandboxSnapshotManager(cache_dir=cache_path)
        cache_key = "test-cache-key-123"

        assert not mgr.has_snapshot(cache_key)
        saved = mgr.save_snapshot(cache_key, src_path, deps_fingerprint="fp1")
        assert saved is True
        assert mgr.has_snapshot(cache_key)

        # Restore into destination
        restored = mgr.restore_snapshot(cache_key, dst_path)
        assert restored is True
        assert (dst_path / "main.py").read_text(encoding="utf-8") == "print('hello world')"
        assert (dst_path / "sub" / "lib.py").read_text(encoding="utf-8") == "X = 42"


def test_cache_pruning():
    with tempfile.TemporaryDirectory() as cache_dir, tempfile.TemporaryDirectory() as src_dir:
        mgr = SandboxSnapshotManager(cache_dir=Path(cache_dir))
        src_path = Path(src_dir)
        (src_path / "file.txt").write_text("sample", encoding="utf-8")

        # Save 4 snapshots
        for i in range(4):
            mgr.save_snapshot(f"key-{i}", src_path, f"fp-{i}")

        assert len(list(Path(cache_dir).iterdir())) == 4
        # Prune to max 2
        pruned = mgr.prune_cache(max_snapshots=2)
        assert pruned == 2
        assert len(list(Path(cache_dir).iterdir())) == 2
