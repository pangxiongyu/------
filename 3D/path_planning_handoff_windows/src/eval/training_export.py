from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean

from src.marl.train_mappo import CheckpointEvalRecord, TrainingStats


def export_training_stats_csv(stats: TrainingStats, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        fieldnames = [
            "episode",
            "episode_reward",
            "scaled_episode_reward",
            "policy_loss",
            "value_loss",
            "return_mean",
            "return_std",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in stats.rows():
            writer.writerow(row)


def plot_training_stats(stats: TrainingStats, path: str | Path) -> None:
    import matplotlib.pyplot as plt

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    episodes = list(range(1, len(stats.episode_rewards) + 1))
    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    axes[0].plot(episodes, stats.episode_rewards, marker="o", label="raw")
    axes[0].plot(episodes, stats.scaled_episode_rewards, marker="x", label="scaled")
    axes[0].set_ylabel("reward")
    axes[0].legend()
    axes[0].set_title("MAPPO prototype training")
    axes[1].plot(episodes, stats.policy_losses, marker="o", color="tab:orange")
    axes[1].set_ylabel("policy loss")
    axes[2].plot(episodes, stats.value_losses, marker="o", color="tab:green")
    axes[2].set_ylabel("value loss")
    axes[2].set_xlabel("episode")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def export_policy_eval_csv(metrics: dict[str, float], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def export_checkpoint_eval_history(
    records: list[CheckpointEvalRecord],
    csv_path: str | Path,
    markdown_path: str | Path,
) -> None:
    if not records:
        return
    rows = [record.row() for record in records]
    fieldnames = list(rows[0].keys())
    output_csv = Path(csv_path)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        " | ".join(fieldnames),
        " | ".join(["---"] * len(fieldnames)),
    ]
    for row in rows:
        lines.append(" | ".join(_format_float(float(row[name])) for name in fieldnames))
    Path(markdown_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_training_run(
    stats: TrainingStats,
    eval_metrics: dict[str, float],
) -> dict[str, float]:
    if not stats.episode_rewards:
        return {
            "episode_count": 0.0,
            **{key: float(value) for key, value in eval_metrics.items()},
        }

    summary = {
        "episode_count": float(len(stats.episode_rewards)),
        "final_episode_reward": stats.episode_rewards[-1],
        "best_episode_reward": max(stats.episode_rewards),
        "mean_episode_reward": mean(stats.episode_rewards),
        "final_scaled_episode_reward": stats.scaled_episode_rewards[-1],
        "mean_scaled_episode_reward": mean(stats.scaled_episode_rewards),
        "final_policy_loss": stats.policy_losses[-1],
        "mean_policy_loss": mean(stats.policy_losses),
        "final_value_loss": stats.value_losses[-1],
        "mean_value_loss": mean(stats.value_losses),
        "max_value_loss": max(stats.value_losses),
        "final_return_mean": stats.return_means[-1],
        "final_return_std": stats.return_stds[-1],
    }
    summary.update({key: float(value) for key, value in eval_metrics.items()})
    return summary


def export_training_summary(
    stats: TrainingStats,
    eval_metrics: dict[str, float],
    output_dir: str | Path,
) -> dict[str, float]:
    summary = summarize_training_run(stats, eval_metrics)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    _write_metric_csv(summary, output_path / "training_summary.csv")
    _write_metric_markdown(summary, output_path / "training_summary.md")
    return summary


def _write_metric_csv(metrics: dict[str, float], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def _write_metric_markdown(metrics: dict[str, float], path: str | Path) -> None:
    lines = ["metric | value", "--- | ---"]
    for key, value in metrics.items():
        lines.append(f"{key} | {_format_float(value)}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_float(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.4f}"
