from __future__ import annotations

from examples.run_mappo_experiments import _experiment_selection_key, deep_merge


def test_mappo_experiment_deep_merge_preserves_nested_defaults() -> None:
    base = {
        "mappo": {"episodes": 3, "ppo_epochs": 2, "learning_rate": 0.0003},
        "marl": {"route_strategies": ["direct", "weather_grid"]},
    }
    overrides = {"mappo": {"episodes": 5}}

    merged = deep_merge(base, overrides)

    assert merged["mappo"] == {
        "episodes": 5,
        "ppo_epochs": 2,
        "learning_rate": 0.0003,
    }
    assert merged["marl"] == {"route_strategies": ["direct", "weather_grid"]}
    assert base["mappo"]["episodes"] == 3


def test_experiment_selection_key_can_prioritize_path_cost() -> None:
    high_reward = {
        "best_mean_completed_task_count": 5.0,
        "best_mean_total_reward": 420.0,
        "best_mean_total_path_cost": 8000.0,
    }
    low_cost = {
        "best_mean_completed_task_count": 5.0,
        "best_mean_total_reward": 400.0,
        "best_mean_total_path_cost": 6000.0,
    }

    assert _experiment_selection_key(low_cost, "path_cost") > _experiment_selection_key(
        high_reward,
        "path_cost",
    )
    assert _experiment_selection_key(high_reward, "reward") > _experiment_selection_key(
        low_cost,
        "reward",
    )


def test_experiment_selection_key_can_prioritize_trackability() -> None:
    low_cost_long_segment = {
        "best_mean_completed_task_count": 5.0,
        "best_mean_total_reward": 420.0,
        "best_mean_total_path_cost": 6000.0,
        "best_mean_peak_segment_distance_km": 3000.0,
    }
    higher_cost_short_segment = {
        "best_mean_completed_task_count": 5.0,
        "best_mean_total_reward": 400.0,
        "best_mean_total_path_cost": 7000.0,
        "best_mean_peak_segment_distance_km": 500.0,
    }

    assert _experiment_selection_key(
        higher_cost_short_segment,
        "trackability",
    ) > _experiment_selection_key(low_cost_long_segment, "trackability")
