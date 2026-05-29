from __future__ import annotations

from src.eval.mappo_checkpoint import mappo_metrics_to_comparable_metrics
from src.marl.train_mappo import aggregate_policy_metrics, checkpoint_selection_key


def test_mappo_metrics_to_comparable_metrics_aligns_with_scenario_metrics() -> None:
    metrics = mappo_metrics_to_comparable_metrics(
        {
            "mean_total_reward": 123.0,
            "mean_completed_task_count": 4.0,
            "mean_average_weather_cost": 0.25,
            "mean_total_path_cost": 900.0,
            "mean_total_distance_km": 880.0,
            "mean_average_max_segment_distance_km": 220.0,
            "mean_peak_segment_distance_km": 400.0,
            "mean_trackability_penalty": 12.5,
            "mean_conflict_count": 1.0,
            "mean_direct_action_count": 1.0,
            "mean_weather_grid_action_count": 2.0,
            "mean_weather_3d_action_count": 1.0,
        },
        task_count=5,
    )

    assert metrics["task_completion_rate"] == 0.8
    assert metrics["completed_task_count"] == 4.0
    assert metrics["rejected_task_count"] == 1.0
    assert metrics["total_reward"] == 123.0
    assert metrics["total_path_cost"] == 900.0
    assert metrics["total_distance_km"] == 880.0
    assert metrics["average_max_segment_distance_km"] == 220.0
    assert metrics["max_segment_distance_km"] == 400.0
    assert metrics["trackability_penalty"] == 12.5
    assert metrics["uav_conflict_count"] == 1.0
    assert metrics["direct_action_count"] == 1.0
    assert metrics["weather_grid_action_count"] == 2.0
    assert metrics["weather_3d_action_count"] == 1.0
    assert metrics["uses_weather_grid_paths"] == 1.0
    assert metrics["uses_weather_3d_paths"] == 1.0


def test_checkpoint_selection_key_prioritizes_completion_then_reward_then_cost() -> None:
    lower_completion = {
        "mean_completed_task_count": 4.0,
        "mean_total_reward": 999.0,
        "mean_total_path_cost": 1.0,
    }
    higher_reward = {
        "mean_completed_task_count": 5.0,
        "mean_total_reward": 100.0,
        "mean_total_path_cost": 1000.0,
    }
    lower_cost = {
        "mean_completed_task_count": 5.0,
        "mean_total_reward": 100.0,
        "mean_total_path_cost": 900.0,
    }

    assert checkpoint_selection_key(higher_reward) > checkpoint_selection_key(lower_completion)
    assert checkpoint_selection_key(lower_cost) > checkpoint_selection_key(higher_reward)


def test_checkpoint_selection_key_can_prioritize_path_cost() -> None:
    high_reward = {
        "mean_completed_task_count": 5.0,
        "mean_total_reward": 500.0,
        "mean_total_path_cost": 8000.0,
    }
    low_cost = {
        "mean_completed_task_count": 5.0,
        "mean_total_reward": 400.0,
        "mean_total_path_cost": 6000.0,
    }

    assert checkpoint_selection_key(low_cost, "path_cost") > checkpoint_selection_key(
        high_reward,
        "path_cost",
    )
    assert checkpoint_selection_key(high_reward, "reward") > checkpoint_selection_key(
        low_cost,
        "reward",
    )


def test_checkpoint_selection_key_can_prioritize_trackability_proxy() -> None:
    low_cost_long_segment = {
        "mean_completed_task_count": 5.0,
        "mean_total_reward": 500.0,
        "mean_total_path_cost": 6000.0,
        "mean_peak_segment_distance_km": 3000.0,
    }
    higher_cost_short_segment = {
        "mean_completed_task_count": 5.0,
        "mean_total_reward": 450.0,
        "mean_total_path_cost": 7000.0,
        "mean_peak_segment_distance_km": 500.0,
    }

    assert checkpoint_selection_key(
        higher_cost_short_segment,
        "trackability",
    ) > checkpoint_selection_key(low_cost_long_segment, "trackability")


def test_aggregate_policy_metrics_averages_validation_scenarios() -> None:
    metrics = aggregate_policy_metrics(
        [
            {"mean_total_reward": 10.0, "mean_total_path_cost": 100.0},
            {"mean_total_reward": 20.0, "mean_total_path_cost": 200.0},
        ]
    )

    assert metrics["validation_scenario_count"] == 2.0
    assert metrics["mean_total_reward"] == 15.0
    assert metrics["mean_total_path_cost"] == 150.0
