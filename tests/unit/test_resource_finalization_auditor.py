"""Unit tests for Differential Resource Finalization Auditor (Amur 2025 / ICSE 2026)."""

import pytest
from services.resource_finalization_auditor import (
    DifferentialResourceFinalizationAuditor,
    LeakHazard,
    ResourceAuditReport,
)


def test_audit_empty_code():
    auditor = DifferentialResourceFinalizationAuditor()
    report = auditor.audit("")
    assert report.has_leaks is False
    assert report.safety_score == 1.0
    assert report.unfinalized_count == 0
    assert len(report.hazards) == 0


def test_audit_safe_with_open():
    auditor = DifferentialResourceFinalizationAuditor()
    code = """
def read_config(path: str) -> str:
    with open(path, "r") as f:
        return f.read()
"""
    report = auditor.audit(code)
    assert report.has_leaks is False
    assert report.safety_score == 1.0
    assert report.unfinalized_count == 0
    assert len(report.hazards) == 1
    assert report.hazards[0].is_safely_finalized is True
    assert report.hazards[0].resource_type == "file_handle"


def test_audit_unclosed_bare_open():
    auditor = DifferentialResourceFinalizationAuditor()
    code = """
def load_data(path: str) -> str:
    f = open(path, "r")
    data = f.read()
    return data
"""
    report = auditor.audit(code)
    assert report.has_leaks is True
    assert report.safety_score == 0.0
    assert report.unfinalized_count == 1
    hazard = report.hazards[0]
    assert hazard.is_safely_finalized is False
    assert hazard.assigned_var == "f"
    assert "Wrap 'open()'" in hazard.remediation_suggestion
    assert report.remediated_code is not None
    assert "with open(path, \"r\") as f:" in report.remediated_code


def test_audit_bare_open_with_explicit_close():
    auditor = DifferentialResourceFinalizationAuditor()
    code = """
def load_data_safe(path: str) -> str:
    f = open(path, "r")
    try:
        return f.read()
    finally:
        f.close()
"""
    report = auditor.audit(code)
    assert report.has_leaks is False
    assert report.safety_score == 1.0
    assert report.unfinalized_count == 0
    assert report.hazards[0].is_safely_finalized is True


def test_audit_database_connection_leak():
    auditor = DifferentialResourceFinalizationAuditor()
    code = """
import sqlite3

def get_user_record(uid: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (uid,))
    return cursor.fetchone()
"""
    report = auditor.audit(code)
    assert report.has_leaks is True
    assert report.unfinalized_count == 1
    hazard = report.hazards[0]
    assert hazard.resource_type == "database_connection"
    assert hazard.target_call == "sqlite3.connect"
    assert hazard.is_safely_finalized is False


def test_auto_remediate_bare_opens_formatting():
    auditor = DifferentialResourceFinalizationAuditor()
    code = """
def process():
    file_ptr = open('records.csv')
    return file_ptr.readline()
"""
    report = auditor.audit(code)
    assert report.has_leaks is True
    assert report.remediated_code is not None
    assert "with open('records.csv') as file_ptr:" in report.remediated_code
