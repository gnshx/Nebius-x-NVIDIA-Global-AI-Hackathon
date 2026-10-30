"""Unit tests for SandboxLayeredOverlayManager (SWE-bench / OpenHands CoW 2026)."""

import pytest
from pathlib import Path
from services.sandbox_layered_overlay import SandboxLayeredOverlayManager, OverlaySession


def test_overlay_session_creation_and_file_isolation(tmp_path):
    base_repo = tmp_path / "base_repo"
    base_repo.mkdir()
    (base_repo / "main.py").write_text("print('hello world')", encoding="utf-8")
    (base_repo / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")

    manager = SandboxLayeredOverlayManager(root_temp_dir=tmp_path / "overlays")
    session = manager.create_overlay_session(base_dir=base_repo, session_id="test-session-1")

    assert session.session_id == "test-session-1"
    assert session.read_overlay_file("main.py") == "print('hello world')"

    # Mutate a file in overlay
    session.write_overlay_file("main.py", "print('patched world')")
    assert session.read_overlay_file("main.py") == "print('patched world')"
    # Base file MUST remain untouched
    assert (base_repo / "main.py").read_text(encoding="utf-8") == "print('hello world')"
    assert "main.py" in session.list_modified_files()

    session.destroy()
    assert session._is_active is False


def test_overlay_manager_destroy_all(tmp_path):
    base_repo = tmp_path / "base_repo"
    base_repo.mkdir()
    (base_repo / "test.txt").write_text("data", encoding="utf-8")

    manager = SandboxLayeredOverlayManager(root_temp_dir=tmp_path / "overlays")
    s1 = manager.create_overlay_session(base_repo, "s1")
    s2 = manager.create_overlay_session(base_repo, "s2")

    assert manager.get_session("s1") is not None
    assert manager.get_session("s2") is not None

    manager.destroy_all()
    assert manager.get_session("s1") is None
    assert manager.get_session("s2") is None


def test_overlay_session_to_dict(tmp_path):
    base_repo = tmp_path / "base_repo"
    base_repo.mkdir()
    (base_repo / "file.txt").write_text("content", encoding="utf-8")

    manager = SandboxLayeredOverlayManager(root_temp_dir=tmp_path / "overlays")
    session = manager.create_overlay_session(base_repo, "dict-test")
    session.write_overlay_file("new_file.txt", "new")

    d = session.to_dict()
    assert d["session_id"] == "dict-test"
    assert "new_file.txt" in d["modified_files"]
    assert d["is_active"] is True
    session.destroy()
