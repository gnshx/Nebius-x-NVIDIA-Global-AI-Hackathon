"""Unit tests for RepoMedic's DynamicSamplingAdapter service."""

from services.sampling_adapter import DynamicSamplingAdapter


def test_first_shot_canonical_deterministic():
    cfg = DynamicSamplingAdapter.calibrate(iteration=0)
    assert cfg.temperature == 0.1
    assert cfg.top_p == 0.95
    assert cfg.enable_thinking is True
    assert cfg.reasoning_budget_tokens == 2048
    assert cfg.sampling_mode == "CANONICAL_DETERMINISTIC"


def test_iteration_1_improved_refinement():
    cfg = DynamicSamplingAdapter.calibrate(iteration=1, delta_verdict="IMPROVED")
    assert cfg.temperature == 0.2
    assert cfg.reasoning_budget_tokens == 4096
    assert cfg.sampling_mode == "TARGETED_REFINEMENT"


def test_iteration_1_regression_recovery():
    cfg = DynamicSamplingAdapter.calibrate(iteration=1, delta_verdict="REGRESSED")
    assert cfg.temperature == 0.35
    assert cfg.top_p == 0.90
    assert cfg.reasoning_budget_tokens == 6144
    assert cfg.sampling_mode == "REGRESSION_RECOVERY"


def test_iteration_2_exploratory_boundary():
    cfg = DynamicSamplingAdapter.calibrate(iteration=2)
    assert cfg.temperature == 0.5
    assert cfg.top_p == 0.85
    assert cfg.reasoning_budget_tokens == 8192
    assert cfg.sampling_mode == "EXPLORATORY_BOUNDARY"


def test_sampling_config_serialization():
    cfg = DynamicSamplingAdapter.calibrate(iteration=0)
    d = cfg.to_dict()
    assert d["temperature"] == 0.1
    assert d["sampling_mode"] == "CANONICAL_DETERMINISTIC"
    assert "rationale" in d
    assert d["reasoning_budget_tokens"] == 2048
