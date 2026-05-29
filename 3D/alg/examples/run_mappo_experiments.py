from __future__ import annotations

import argparse
import csv
from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario_from_config, load_config
from src.eval.training_export import (
    export_checkpoint_eval_history,
    export_policy_eval_csv,
    export_training_stats_csv,
    plot_training_stats,
    summarize_training_run,
)
from src.marl.scenario_env import build_marl_env_from_scenario
from src.marl.train_mappo import MAPPOPrototypeTrainer


def deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_suite(path: str | Path) -> dict[str, Any]:
    suite_path = Path(path)
    with suite_path.open("r", encoding="utf-8") as file:
        suite = yaml.safe_load(file) or {}
    suite["_suite_path"] = str(suite_path)
    suite["_root"] = str(suite_path.resolve().parents[1])
    return suite


def train_one_experiment(
    name: str,
    config: dict[str, Any],
    root: Path,
    output_dir: Path,
    eval_env_factories: list | None = None,
    checkpoint_selection_mode: str = "reward",
) -> dict[str, str | float]:
    scenario = build_scenario_from_config(config, root=root)
    mappo_config = scenario.config.get("mappo", {})
    marl_config = scenario.config.get("marl", {})
    reward_config = marl_config.get("reward", {})
    seed = mappo_config.get("seed")
    seed_value = int(seed) if seed is not None else None
    trainer = MAPPOPrototypeTrainer(
        lambda: build_marl_env_from_scenario(scenario),
        episodes=int(mappo_config.get("episodes", 10)),
        gamma=float(mappo_config.get("gamma", 0.95)),
        clip_ratio=float(mappo_config.get("clip_ratio", 0.2)),
        ppo_epochs=int(mappo_config.get("ppo_epochs", 2)),
        lr=float(mappo_config.get("learning_rate", 3e-4)),
        reward_scale=float(mappo_config.get("reward_scale", 0.01)),
        normalize_value_targets=bool(mappo_config.get("normalize_value_targets", True)),
        mask_wait_when_tasks_available=bool(
            mappo_config.get("mask_wait_when_tasks_available", True)
        ),
        seed=seed_value,
    )
    experiment_dir = output_dir / name
    stats, checkpoint_records = trainer.train_with_eval_checkpoints(
        experiment_dir / "best_checkpoint.pt",
        eval_interval=int(mappo_config.get("eval_interval", 1)),
        eval_episodes=int(mappo_config.get("eval_episodes", 3)),
        eval_env_factories=eval_env_factories,
        checkpoint_selection_mode=checkpoint_selection_mode,
    )
    eval_metrics = trainer.evaluate_policy(
        episodes=int(mappo_config.get("eval_episodes", 3)),
        deterministic=True,
    )

    trainer.save_checkpoint(experiment_dir / "mappo_checkpoint.pt")
    export_training_stats_csv(stats, experiment_dir / "training_history.csv")
    export_checkpoint_eval_history(
        checkpoint_records,
        experiment_dir / "checkpoint_eval_history.csv",
        experiment_dir / "checkpoint_eval_history.md",
    )
    plot_training_stats(stats, experiment_dir / "training_curves.png")
    export_policy_eval_csv(eval_metrics, experiment_dir / "policy_eval.csv")
    summary = summarize_training_run(stats, eval_metrics)
    _write_metric_csv(summary, experiment_dir / "training_summary.csv")
    _write_metric_markdown(summary, experiment_dir / "training_summary.md")
    best_record = next((record for record in reversed(checkpoint_records) if record.is_best), None)
    if best_record is not None:
        export_policy_eval_csv(best_record.metrics, experiment_dir / "best_policy_eval.csv")

    return {
        "experiment": name,
        "seed": -1.0 if seed_value is None else float(seed_value),
        "episodes_config": float(mappo_config.get("episodes", 10)),
        "ppo_epochs": float(mappo_config.get("ppo_epochs", 2)),
        "learning_rate": float(mappo_config.get("learning_rate", 3e-4)),
        "reward_scale": float(mappo_config.get("reward_scale", 0.01)),
        "task_complete_reward": float(reward_config.get("task_complete_reward", 100.0)),
        "distance_weight": float(reward_config.get("distance_weight", 10.0)),
        "weather_weight": float(reward_config.get("weather_weight", 20.0)),
        "energy_weight": float(reward_config.get("energy_weight", 5.0)),
        "risk_weight": float(reward_config.get("risk_weight", 1.0)),
        "path_cost_weight": float(reward_config.get("path_cost_weight", 0.0)),
        "trackability_weight": float(reward_config.get("trackability_weight", 0.0)),
        "validation_scenario_count": 0.0 if not eval_env_factories else float(len(eval_env_factories)),
        "best_eval_episode": 0.0 if best_record is None else float(best_record.episode),
        **{
            f"best_{key}": float(value)
            for key, value in (best_record.metrics if best_record is not None else {}).items()
        },
        **summary,
    }


def write_experiment_summary(
    rows: list[dict[str, str | float]],
    output_dir: Path,
    selection_mode: str = "reward",
) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "mappo_experiment_summary.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        " | ".join(fieldnames),
        " | ".join(["---"] * len(fieldnames)),
    ]
    for row in rows:
        lines.append(" | ".join(_format_value(row[name]) for name in fieldnames))
    (output_dir / "mappo_experiment_summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    best = max(rows, key=lambda row: _experiment_selection_key(row, selection_mode))
    best_lines = [
        "# Best MAPPO Experiment",
        "",
        f"selection_mode: {selection_mode}",
        f"experiment: {best['experiment']}",
        f"checkpoint: {output_dir / str(best['experiment']) / 'best_checkpoint.pt'}",
        f"best_eval_episode: {_format_value(best['best_eval_episode'])}",
        f"mean_completed_task_count: {_format_value(best['best_mean_completed_task_count'])}",
        f"mean_total_reward: {_format_value(best['best_mean_total_reward'])}",
        f"mean_total_path_cost: {_format_value(best['best_mean_total_path_cost'])}",
        f"mean_peak_segment_distance_km: {_format_value(best.get('best_mean_peak_segment_distance_km', 0.0))}",
        f"mean_trackability_penalty: {_format_value(best.get('best_mean_trackability_penalty', 0.0))}",
        f"mean_weather_grid_action_count: {_format_value(best['best_mean_weather_grid_action_count'])}",
        f"mean_weather_3d_action_count: {_format_value(best['best_mean_weather_3d_action_count'])}",
    ]
    (output_dir / "best_experiment.md").write_text(
        "\n".join(best_lines) + "\n",
        encoding="utf-8",
    )


def _experiment_selection_key(
    row: dict[str, str | float],
    selection_mode: str,
) -> tuple[float, ...]:
    completed = float(row.get("best_mean_completed_task_count", row.get("mean_completed_task_count", 0.0)))
    reward = float(row.get("best_mean_total_reward", row.get("mean_total_reward", 0.0)))
    path_cost = float(row.get("best_mean_total_path_cost", row.get("mean_total_path_cost", 0.0)))
    peak_segment = float(
        row.get("best_mean_peak_segment_distance_km", row.get("mean_peak_segment_distance_km", 0.0))
    )
    if selection_mode == "path_cost":
        return (completed, -path_cost, reward)
    if selection_mode in {"trackability", "mpc_proxy"}:
        return (completed, -peak_segment, -path_cost, reward)
    return (completed, reward, -path_cost)


def build_validation_env_factories(
    base_config: dict[str, Any],
    root: Path,
    validation_suite_path: str | Path | None,
) -> list:
    if validation_suite_path is None:
        return []
    suite_path = Path(validation_suite_path)
    if not suite_path.is_absolute():
        suite_path = root / suite_path
    validation_suite = load_suite(suite_path)
    env_factories = []
    for experiment in validation_suite.get("experiments", []):
        validation_config = deep_merge(base_config, experiment.get("overrides", {}))
        scenario = build_scenario_from_config(validation_config, root=root)
        env_factories.append(lambda scenario=scenario: build_marl_env_from_scenario(scenario))
    return env_factories


def _write_metric_csv(metrics: dict[str, float], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def _write_metric_markdown(metrics: dict[str, float], path: str | Path) -> None:
    lines = ["metric | value", "--- | ---"]
    for key, value in metrics.items():
        lines.append(f"{key} | {_format_value(value)}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_value(value: str | float) -> str:
    if isinstance(value, str):
        return value
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a MAPPO hyperparameter experiment suite.")
    parser.add_argument(
        "--suite",
        default=str(ROOT / "configs" / "mappo_experiments.yaml"),
        help="Path to MAPPO experiment YAML.",
    )
    parser.add_argument(
        "--max-experiments",
        type=int,
        default=None,
        help="Optional cap for quick smoke checks.",
    )
    args = parser.parse_args()

    suite = load_suite(args.suite)
    root = Path(suite["_root"])
    base_config = load_config(root / suite.get("base_config", "configs/default.yaml"))
    output_dir = root / suite.get("output_dir", "outputs/mappo_experiments")
    experiments = suite.get("experiments", [])
    checkpoint_selection_mode = str(
        suite.get("checkpoint_selection_mode", suite.get("selection_mode", "reward"))
    )
    if args.max_experiments is not None:
        experiments = experiments[: args.max_experiments]
    if not experiments:
        raise SystemExit("No MAPPO experiments configured.")

    rows: list[dict[str, str | float]] = []
    for experiment in experiments:
        name = str(experiment["name"])
        config = deep_merge(base_config, experiment.get("overrides", {}))
        eval_env_factories = build_validation_env_factories(
            config,
            root=root,
            validation_suite_path=suite.get("validation_suite"),
        )
        print(f"\nMAPPO experiment: {name}")
        row = train_one_experiment(
            name,
            config,
            root=root,
            output_dir=output_dir,
            eval_env_factories=eval_env_factories,
            checkpoint_selection_mode=checkpoint_selection_mode,
        )
        rows.append(row)
        print(
            {
                "final_episode_reward": round(float(row["final_episode_reward"]), 4),
                "mean_total_reward": round(float(row["mean_total_reward"]), 4),
                "mean_completed_task_count": round(float(row["mean_completed_task_count"]), 4),
                "mean_total_path_cost": round(float(row["mean_total_path_cost"]), 4),
            }
        )

    write_experiment_summary(rows, output_dir, selection_mode=str(suite.get("selection_mode", "reward")))
    print("\nMAPPO experiments exported")
    print(
        {
            "output_dir": str(output_dir),
            "summary_csv": str(output_dir / "mappo_experiment_summary.csv"),
            "summary_md": str(output_dir / "mappo_experiment_summary.md"),
        }
    )


if __name__ == "__main__":
    main()
