from __future__ import annotations

from src.marl.action_space import (
    build_task_actions,
    encode_task_action,
    parse_task_action,
    parse_task_action_with_strategy,
)


def test_height_action_round_trip() -> None:
    action = encode_task_action("T1", 100.0)
    assert action == "T1@100m"
    task_id, height = parse_task_action(action)
    assert task_id == "T1"
    assert height == 100.0


def test_build_task_actions_with_height_layers() -> None:
    actions = build_task_actions(["T1", "T2"], [10.0, 100.0])
    assert actions == ["wait", "T1@10m", "T1@100m", "T2@10m", "T2@100m"]


def test_strategy_action_round_trip() -> None:
    action = encode_task_action("T2", 10.0, "weather_grid")
    assert action == "T2@10m#weather_grid"
    task_id, height, strategy = parse_task_action_with_strategy(action)
    assert task_id == "T2"
    assert height == 10.0
    assert strategy == "weather_grid"


def test_build_task_actions_with_strategies() -> None:
    actions = build_task_actions(["T1"], [10.0], ["direct", "weather_grid"])
    assert actions == ["wait", "T1@10m#direct", "T1@10m#weather_grid"]
