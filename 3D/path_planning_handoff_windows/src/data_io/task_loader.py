from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.core.schemas import TaskState, WeatherCell


def _optional_float(row: pd.Series, column: str, default: float | None = None) -> float | None:
    if column not in row:
        return default
    value = row[column]
    if pd.isna(value):
        return default
    return float(value)


def load_tasks_csv(path: str | Path) -> list[TaskState]:
    frame = pd.read_csv(path)
    required = {"task_id", "target_lat", "target_lon", "target_height_m"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Task file is missing columns: {missing}")
    tasks: list[TaskState] = []
    for _, row in frame.iterrows():
        tasks.append(
            TaskState(
                task_id=str(row["task_id"]),
                target_lat=float(row["target_lat"]),
                target_lon=float(row["target_lon"]),
                target_height_m=float(row["target_height_m"]),
                payload_g=float(_optional_float(row, "payload_g", 0.0) or 0.0),
                deadline_s=_optional_float(row, "deadline_s"),
                priority=float(_optional_float(row, "priority", 1.0) or 1.0),
            )
        )
    return tasks


def make_demo_tasks(cells: list[WeatherCell], payload_g: float = 200.0) -> list[TaskState]:
    tasks: list[TaskState] = []
    for index, cell in enumerate(cells, start=1):
        tasks.append(
            TaskState(
                task_id=f"T{index}",
                target_lat=cell.latitude,
                target_lon=cell.longitude,
                target_height_m=cell.height_m,
                payload_g=payload_g,
                priority=1.0,
            )
        )
    return tasks
