from __future__ import annotations

from src.eval.metrics import compare_metric_tables


def print_comparison(named_metrics: dict[str, dict[str, float]]) -> None:
    print(compare_metric_tables(named_metrics))

