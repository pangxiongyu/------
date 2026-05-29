from __future__ import annotations

from examples.run_batch_experiments import deep_merge


def test_deep_merge_preserves_nested_base_values() -> None:
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    overrides = {"a": {"y": 4}}
    merged = deep_merge(base, overrides)
    assert merged == {"a": {"x": 1, "y": 4}, "b": 3}
    assert base == {"a": {"x": 1, "y": 2}, "b": 3}

