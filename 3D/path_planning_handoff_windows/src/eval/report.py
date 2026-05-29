from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path


DEFAULT_SUMMARY_METRICS = [
    "task_completion_rate",
    "completed_task_count",
    "total_path_cost",
    "total_distance_km",
    "average_weather_cost",
    "uav_conflict_count",
    "direct_action_count",
    "weather_grid_action_count",
    "weather_3d_action_count",
]


def load_batch_metrics_csv(path: str | Path) -> list[dict[str, str | float]]:
    rows: list[dict[str, str | float]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(
                {
                    "experiment": row["experiment"],
                    "method": row["method"],
                    "metric": row["metric"],
                    "value": float(row["value"]),
                }
            )
    return rows


def summarize_batch_metrics(
    rows: list[dict[str, str | float]],
    metrics: list[str] | None = None,
) -> list[dict[str, str | float]]:
    selected_metrics = metrics or DEFAULT_SUMMARY_METRICS
    grouped: OrderedDict[tuple[str, str], dict[str, str | float]] = OrderedDict()

    for row in rows:
        experiment = str(row["experiment"])
        method = str(row["method"])
        metric = str(row["metric"])
        if metric not in selected_metrics:
            continue
        key = (experiment, method)
        if key not in grouped:
            grouped[key] = {
                "experiment": experiment,
                "method": method,
                **{name: 0.0 for name in selected_metrics},
            }
        grouped[key][metric] = float(row["value"])

    return list(grouped.values())


def write_summary_csv(
    rows: list[dict[str, str | float]],
    path: str | Path,
    metrics: list[str] | None = None,
) -> None:
    selected_metrics = metrics or DEFAULT_SUMMARY_METRICS
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["experiment", "method", *selected_metrics])
        writer.writeheader()
        writer.writerows(rows)


def write_summary_markdown(
    rows: list[dict[str, str | float]],
    path: str | Path,
    metrics: list[str] | None = None,
) -> None:
    selected_metrics = metrics or DEFAULT_SUMMARY_METRICS
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["experiment", "method", *selected_metrics]
    lines = [
        " | ".join(headers),
        " | ".join(["---"] * len(headers)),
    ]
    for row in rows:
        values = [str(row["experiment"]), str(row["method"])]
        values.extend(_format_value(float(row[metric])) for metric in selected_metrics)
        lines.append(" | ".join(values))
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_batch_summary(
    long_metrics_path: str | Path,
    output_dir: str | Path,
    metrics: list[str] | None = None,
) -> list[dict[str, str | float]]:
    rows = load_batch_metrics_csv(long_metrics_path)
    summary_rows = summarize_batch_metrics(rows, metrics=metrics)
    output_path = Path(output_dir)
    write_summary_csv(summary_rows, output_path / "batch_summary.csv", metrics=metrics)
    write_summary_markdown(summary_rows, output_path / "batch_summary.md", metrics=metrics)
    return summary_rows


def _format_value(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.4f}"
