from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.run_mappo_train import make_env
from src.data_io.scenario_loader import build_scenario
from src.eval.training_export import export_policy_eval_csv
from src.marl.train_mappo import MAPPOPrototypeTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a saved MAPPO prototype checkpoint.")
    parser.add_argument("--config", default=str(ROOT / "configs" / "default.yaml"))
    parser.add_argument(
        "--checkpoint",
        default=str(ROOT / "outputs" / "mappo_train" / "mappo_checkpoint.pt"),
    )
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "mappo_train" / "policy_eval_loaded.csv"))
    args = parser.parse_args()

    scenario = build_scenario(args.config)
    mappo_config = scenario.config.get("mappo", {})
    trainer = MAPPOPrototypeTrainer(
        lambda: make_env(args.config),
        episodes=1,
        ppo_epochs=1,
        mask_wait_when_tasks_available=bool(
            mappo_config.get("mask_wait_when_tasks_available", True)
        ),
        seed=int(mappo_config["seed"]) if "seed" in mappo_config else None,
    )
    trainer.load_checkpoint(args.checkpoint)
    metrics = trainer.evaluate_policy(episodes=args.episodes, deterministic=True)
    export_policy_eval_csv(metrics, args.output)
    print("loaded_checkpoint:", args.checkpoint)
    print("metrics:", {key: round(value, 4) for key, value in metrics.items()})
    print("exported:", args.output)


if __name__ == "__main__":
    main()
