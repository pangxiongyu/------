from __future__ import annotations

from pathlib import Path

from src.data_io.task_loader import load_tasks_csv


def test_load_tasks_csv_reads_required_and_optional_fields(tmp_path: Path) -> None:
    task_file = tmp_path / "tasks.csv"
    task_file.write_text(
        "task_id,target_lat,target_lon,target_height_m,payload_g,deadline_s,priority\n"
        "T1,30.0,110.0,10,200,600,1.5\n",
        encoding="utf-8",
    )
    tasks = load_tasks_csv(task_file)
    assert len(tasks) == 1
    assert tasks[0].task_id == "T1"
    assert tasks[0].payload_g == 200.0
    assert tasks[0].deadline_s == 600.0
    assert tasks[0].priority == 1.5

