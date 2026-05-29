from __future__ import annotations

from src.eval.training_export import summarize_training_run
from src.marl.train_mappo import TrainingStats


def test_training_stats_rows() -> None:
    stats = TrainingStats(
        episode_rewards=[1.0, 2.0],
        scaled_episode_rewards=[0.01, 0.02],
        policy_losses=[0.1, 0.2],
        value_losses=[3.0, 4.0],
        return_means=[0.5, 0.6],
        return_stds=[0.7, 0.8],
    )
    assert stats.rows() == [
        {
            "episode": 1.0,
            "episode_reward": 1.0,
            "scaled_episode_reward": 0.01,
            "policy_loss": 0.1,
            "value_loss": 3.0,
            "return_mean": 0.5,
            "return_std": 0.7,
        },
        {
            "episode": 2.0,
            "episode_reward": 2.0,
            "scaled_episode_reward": 0.02,
            "policy_loss": 0.2,
            "value_loss": 4.0,
            "return_mean": 0.6,
            "return_std": 0.8,
        },
    ]


def test_summarize_training_run_combines_training_and_eval_metrics() -> None:
    stats = TrainingStats(
        episode_rewards=[100.0, 120.0],
        scaled_episode_rewards=[1.0, 1.2],
        policy_losses=[0.1, 0.2],
        value_losses=[0.8, 0.6],
        return_means=[1.5, 1.7],
        return_stds=[0.3, 0.4],
    )

    summary = summarize_training_run(
        stats,
        {
            "mean_total_reward": 110.0,
            "mean_conflict_count": 0.0,
        },
    )

    assert summary["episode_count"] == 2.0
    assert summary["final_episode_reward"] == 120.0
    assert summary["best_episode_reward"] == 120.0
    assert summary["mean_value_loss"] == 0.7
    assert summary["mean_total_reward"] == 110.0
    assert summary["mean_conflict_count"] == 0.0
