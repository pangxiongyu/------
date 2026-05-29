from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario
from src.eval.training_export import (
    export_checkpoint_eval_history,
    export_policy_eval_csv,
    export_training_summary,
    export_training_stats_csv,
    plot_training_stats,
)
from src.marl.env import MultiUavTaskEnv
from src.marl.scenario_env import build_marl_env_from_scenario
from src.marl.train_mappo import MAPPOPrototypeTrainer


def make_env(config_path: str | Path = ROOT / "configs" / "default.yaml") -> MultiUavTaskEnv:
    scenario = build_scenario(config_path)
    return build_marl_env_from_scenario(scenario)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the MAPPO prototype policy.")
    parser.add_argument("--config", default=str(ROOT / "configs" / "default.yaml"))
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument("--ppo-epochs", type=int, default=None)
    parser.add_argument("--reward-scale", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-normalize-value-targets", action="store_true")
    parser.add_argument("--output-dir", default=str(ROOT / "outputs" / "mappo_train"))
    args = parser.parse_args()

    scenario = build_scenario(args.config)
    mappo_config = scenario.config.get("mappo", {})
    episodes = args.episodes if args.episodes is not None else int(mappo_config.get("episodes", 10))
    ppo_epochs = args.ppo_epochs if args.ppo_epochs is not None else int(mappo_config.get("ppo_epochs", 2))
    reward_scale = (
        args.reward_scale if args.reward_scale is not None else float(mappo_config.get("reward_scale", 0.01))
    )
    seed = args.seed if args.seed is not None else mappo_config.get("seed")
    seed = int(seed) if seed is not None else None
    normalize_value_targets = (
        bool(mappo_config.get("normalize_value_targets", True))
        and not args.no_normalize_value_targets
    )
    mask_wait_when_tasks_available = bool(
        mappo_config.get("mask_wait_when_tasks_available", True)
    )
    eval_episodes = int(mappo_config.get("eval_episodes", 3))
    eval_interval = int(mappo_config.get("eval_interval", 1))
    checkpoint_selection_mode = str(mappo_config.get("checkpoint_selection_mode", "reward"))
    output_dir = Path(args.output_dir)
    trainer = MAPPOPrototypeTrainer(
        lambda: make_env(args.config),
        episodes=episodes,
        gamma=float(mappo_config.get("gamma", 0.95)),
        clip_ratio=float(mappo_config.get("clip_ratio", 0.2)),
        ppo_epochs=ppo_epochs,
        lr=float(mappo_config.get("learning_rate", 3e-4)),
        reward_scale=reward_scale,
        normalize_value_targets=normalize_value_targets,
        mask_wait_when_tasks_available=mask_wait_when_tasks_available,
        seed=seed,
    )
    stats, checkpoint_records = trainer.train_with_eval_checkpoints(
        output_dir / "best_checkpoint.pt",
        eval_interval=eval_interval,
        eval_episodes=eval_episodes,
        checkpoint_selection_mode=checkpoint_selection_mode,
    )
    eval_metrics = trainer.evaluate_policy(episodes=eval_episodes, deterministic=True)
    trainer.save_checkpoint(output_dir / "mappo_checkpoint.pt")
    export_training_stats_csv(stats, output_dir / "training_history.csv")
    export_checkpoint_eval_history(
        checkpoint_records,
        output_dir / "checkpoint_eval_history.csv",
        output_dir / "checkpoint_eval_history.md",
    )
    plot_training_stats(stats, output_dir / "training_curves.png")
    export_policy_eval_csv(eval_metrics, output_dir / "policy_eval.csv")
    export_training_summary(stats, eval_metrics, output_dir)
    best_record = next((record for record in reversed(checkpoint_records) if record.is_best), None)
    if best_record is not None:
        export_policy_eval_csv(best_record.metrics, output_dir / "best_policy_eval.csv")

    print("device:", trainer.device)
    print("config:", args.config)
    print("action_count:", trainer.action_dim)
    print("reward_scale:", reward_scale)
    print("seed:", seed)
    print("normalize_value_targets:", normalize_value_targets)
    print("mask_wait_when_tasks_available:", mask_wait_when_tasks_available)
    print("eval_interval:", eval_interval)
    print("checkpoint_selection_mode:", checkpoint_selection_mode)
    print("episode_rewards:", [round(value, 3) for value in stats.episode_rewards])
    print("scaled_episode_rewards:", [round(value, 3) for value in stats.scaled_episode_rewards])
    print("policy_losses:", [round(value, 4) for value in stats.policy_losses])
    print("value_losses:", [round(value, 4) for value in stats.value_losses])
    print("return_means:", [round(value, 4) for value in stats.return_means])
    print("return_stds:", [round(value, 4) for value in stats.return_stds])
    print("eval_metrics:", {key: round(value, 4) for key, value in eval_metrics.items()})
    print(
        "exported:",
        {
            "checkpoint": str(output_dir / "mappo_checkpoint.pt"),
            "best_checkpoint": str(output_dir / "best_checkpoint.pt"),
            "history": str(output_dir / "training_history.csv"),
            "checkpoint_eval_history": str(output_dir / "checkpoint_eval_history.csv"),
            "curves": str(output_dir / "training_curves.png"),
            "eval": str(output_dir / "policy_eval.csv"),
            "summary": str(output_dir / "training_summary.md"),
        },
    )


if __name__ == "__main__":
    main()
