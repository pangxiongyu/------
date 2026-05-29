from __future__ import annotations

from src.core.cost_model import normalize, risk_penalty


def test_normalize_clamps_values() -> None:
    assert normalize(-1.0, 0.0, 10.0) == 0.0
    assert normalize(20.0, 0.0, 10.0) == 1.0
    assert normalize(5.0, 0.0, 10.0) == 0.5


def test_risk_penalty_ordering() -> None:
    assert risk_penalty("low") < risk_penalty("medium") < risk_penalty("high")

