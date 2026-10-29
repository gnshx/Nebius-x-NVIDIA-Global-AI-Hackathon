"""Unit tests for Polyglot Project Harness & Ephemeral Worktree Manager."""

import tempfile
from pathlib import Path
import pytest

from services.polyglot_harness import (
    EphemeralWorktreeManager,
    PolyglotDetector,
    ProjectEcosystem,
)


def test_detect_rust_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "Cargo.toml").write_text("[package]\nname = 'test'\nversion = '0.1.0'\n")
        cfg = PolyglotDetector.detect(p)
        assert cfg.ecosystem == ProjectEcosystem.RUST
        assert cfg.manifest_file == "Cargo.toml"
        assert cfg.test_command == "cargo test"


def test_detect_go_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "go.mod").write_text("module example.com/test\ngo 1.21\n")
        cfg = PolyglotDetector.detect(p)
        assert cfg.ecosystem == ProjectEcosystem.GO
        assert cfg.manifest_file == "go.mod"
        assert cfg.test_command == "go test ./..."


def test_detect_typescript_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "package.json").write_text('{"name": "test"}')
        (p / "tsconfig.json").write_text('{"compilerOptions": {}}')
        cfg = PolyglotDetector.detect(p)
        assert cfg.ecosystem == ProjectEcosystem.TYPESCRIPT
        assert cfg.manifest_file == "package.json"
        assert cfg.test_command == "npm test"


def test_detect_javascript_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "package.json").write_text('{"name": "test"}')
        cfg = PolyglotDetector.detect(p)
        assert cfg.ecosystem == ProjectEcosystem.JAVASCRIPT
        assert cfg.manifest_file == "package.json"


def test_detect_python_project_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "pyproject.toml").write_text('[project]\nname = "test"\n')
        cfg = PolyglotDetector.detect(p)
        assert cfg.ecosystem == ProjectEcosystem.PYTHON
        assert cfg.manifest_file == "pyproject.toml"
        assert cfg.test_command == "pytest"
        assert "--tb=short" in cfg.json_report_flags


def test_ephemeral_worktree_manager_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = EphemeralWorktreeManager(tmpdir)
        run_id = "test-run-123"
        wt_path = mgr.create_worktree(run_id)
        assert wt_path.exists()
        assert wt_path.name == run_id

        mgr.remove_worktree(run_id)
        assert not wt_path.exists()
