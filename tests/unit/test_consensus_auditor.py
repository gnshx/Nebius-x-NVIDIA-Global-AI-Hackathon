"""Unit tests for RepoMedic's PatchConsensusAuditor (PROBE/TEX)."""

import pytest
from services.consensus_auditor import PatchConsensusAuditor, ConsensusAuditResult


def test_high_confidence_fix_recommends_automated_merge():
    result = PatchConsensusAuditor.audit(
        oracle_confidence=1.0,
        invariant_score=1.0,
        cleanliness_score=0.95,
        mutation_score=0.90,
        security_passed=True,
    )

    assert isinstance(result, ConsensusAuditResult)
    assert result.dri_score >= 90.0
    assert result.recommendation == "AUTOMATED_MERGE_RECOMMENDED"
    assert result.is_deployable is True
    assert result.breakdown["oracle_confidence"] == 100.0


def test_moderate_confidence_suggests_manual_review():
    result = PatchConsensusAuditor.audit(
        oracle_confidence=0.80,
        invariant_score=0.75,
        cleanliness_score=0.60,
        mutation_score=0.60,
        security_passed=True,
    )

    assert result.recommendation == "MANUAL_REVIEW_SUGGESTED"
    assert result.is_deployable is False
    assert 65.0 <= result.dri_score < 85.0


def test_security_failure_hard_rejects_with_zero_dri():
    result = PatchConsensusAuditor.audit(
        oracle_confidence=1.0,
        invariant_score=1.0,
        cleanliness_score=1.0,
        mutation_score=1.0,
        security_passed=False,
    )

    assert result.dri_score == 0.0
    assert result.recommendation == "REJECTED"
    assert result.is_deployable is False
    assert any("Security gate failed" in d for d in result.details)


def test_consensus_audit_to_dict():
    result = PatchConsensusAuditor.audit()
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "dri_score" in d
    assert "recommendation" in d
    assert "breakdown" in d
