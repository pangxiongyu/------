from __future__ import annotations

from src.eval.report import summarize_batch_metrics


def test_summarize_batch_metrics_keeps_selected_metrics_in_rows() -> None:
    rows = [
        {
            "experiment": "exp_a",
            "method": "marl_greedy",
            "metric": "task_completion_rate",
            "value": 1.0,
        },
        {
            "experiment": "exp_a",
            "method": "marl_greedy",
            "metric": "weather_3d_action_count",
            "value": 2.0,
        },
        {
            "experiment": "exp_a",
            "method": "marl_greedy",
            "metric": "ignored_metric",
            "value": 99.0,
        },
    ]

    summary = summarize_batch_metrics(rows, metrics=["task_completion_rate", "weather_3d_action_count"])

    assert summary == [
        {
            "experiment": "exp_a",
            "method": "marl_greedy",
            "task_completion_rate": 1.0,
            "weather_3d_action_count": 2.0,
        }
    ]
