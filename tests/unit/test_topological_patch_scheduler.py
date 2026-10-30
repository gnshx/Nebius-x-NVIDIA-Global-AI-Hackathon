"""Unit tests for TopologicalPatchScheduler (Multi-SWE-bench 2025/2026)."""

import pytest
from services.topological_patch_scheduler import (
    TopologicalPatchScheduler,
    ScheduledFileChange,
    ScheduleReport,
)


def test_topological_scheduler_single_file():
    files = [{"path": "src/math.py", "operation": "modify", "reason": "fix", "diff": ""}]
    report = TopologicalPatchScheduler.schedule_patch_files(files)
    assert report.total_files == 1
    assert report.is_multi_file_patch is False
    assert report.ordered_files[0].path == "src/math.py"
    assert report.has_circular_dependency is False


def test_topological_scheduler_orders_source_before_tests():
    files = [
        {"path": "tests/test_math.py", "operation": "add", "reason": "regression test", "diff": ""},
        {"path": "src/math.py", "operation": "modify", "reason": "boundary fix", "diff": ""},
    ]
    report = TopologicalPatchScheduler.schedule_patch_files(files)
    assert report.total_files == 2
    assert report.is_multi_file_patch is True
    # Source file must be scheduled before test file
    assert report.ordered_files[0].path == "src/math.py"
    assert report.ordered_files[1].path == "tests/test_math.py"
    assert report.ordered_files[0].is_test_file is False
    assert report.ordered_files[1].is_test_file is True


def test_topological_scheduler_resolves_import_dependencies():
    files = [
        {
            "path": "src/service.py",
            "operation": "modify",
            "reason": "use helper",
            "diff": "+from utils import format_user\n+def run(): pass\n",
        },
        {
            "path": "src/utils.py",
            "operation": "modify",
            "reason": "define helper",
            "diff": "+def format_user(): pass\n",
        },
        {
            "path": "tests/test_service.py",
            "operation": "add",
            "reason": "test service",
            "diff": "",
        },
    ]
    report = TopologicalPatchScheduler.schedule_patch_files(files)
    assert report.total_files == 3
    order = [f.path for f in report.ordered_files]
    # utils.py must precede service.py, and service.py must precede test_service.py
    assert order.index("src/utils.py") < order.index("src/service.py")
    assert order.index("src/service.py") < order.index("tests/test_service.py")


def test_topological_scheduler_handles_empty():
    report = TopologicalPatchScheduler.schedule_patch_files([])
    assert report.total_files == 0
    assert len(report.ordered_files) == 0


def test_topological_report_to_dict():
    item = ScheduledFileChange(0, "a.py", "modify", [], False, "reason")
    rep = ScheduleReport(1, [item], False, [], False)
    d = rep.to_dict()
    assert d["total_files"] == 1
    assert d["ordered_files"][0]["path"] == "a.py"
