from __future__ import annotations

import pandas as pd
import torch

from src.core.schemas import TaskState, UavProfile, UavState
from src.data_io.weather_loader import WeatherMap
from src.marl.action_space import WAIT_ACTION
from src.marl.env import MultiUavTaskEnv
from src.marl.train_mappo import MAPPOPrototypeTrainer


def make_profile() -> UavProfile:
    return UavProfile(
        flight_id=1,
        route="R",
        payload_g=0.0,
        target_altitude_m=10.0,
        window_start_s=0.0,
        window_end_s=1.0,
        pred_voltage_drop_v=0.0,
        pred_avg_current_a=0.0,
        pred_stability_risk=0.0,
        pred_stability_pressure=0.0,
        dynamic_health_score=90.0,
        dynamic_risk_level="low",
    )


def make_env() -> MultiUavTaskEnv:
    weather_map = WeatherMap(
        pd.DataFrame(
            [
                {
                    "time": "t0",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "height_m": 10.0,
                    "cost": 0.1,
                    "wind_speed": 0.0,
                    "wind_direction": 0.0,
                    "temperature_2m": 20.0,
                    "relative_humidity_2m": 50.0,
                    "weather_code": 0.0,
                },
                {
                    "time": "t0",
                    "latitude": 1.0,
                    "longitude": 1.0,
                    "height_m": 10.0,
                    "cost": 0.1,
                    "wind_speed": 0.0,
                    "wind_direction": 0.0,
                    "temperature_2m": 20.0,
                    "relative_humidity_2m": 50.0,
                    "weather_code": 0.0,
                },
            ]
        )
    )
    return MultiUavTaskEnv(
        uavs=[UavState("U1", 0.0, 0.0, 10.0, 500.0, make_profile())],
        tasks=[TaskState("T1", 1.0, 1.0, 10.0, payload_g=100.0)],
        weather_map=weather_map,
        time="t0",
        max_steps=1,
    )


def test_mappo_masks_wait_when_task_actions_are_available() -> None:
    trainer = MAPPOPrototypeTrainer(make_env, episodes=1, ppo_epochs=1)
    wait_index = trainer.action_names.index(WAIT_ACTION)

    mask = trainer._mask_for_agent([WAIT_ACTION, "T1"])

    assert mask[wait_index] is False
    assert any(mask)


def test_mappo_keeps_wait_when_it_is_the_only_available_action() -> None:
    trainer = MAPPOPrototypeTrainer(make_env, episodes=1, ppo_epochs=1)
    wait_index = trainer.action_names.index(WAIT_ACTION)

    mask = trainer._mask_for_agent([WAIT_ACTION])

    assert mask[wait_index] is True


def test_mappo_seed_reproduces_initial_model_parameters() -> None:
    trainer_a = MAPPOPrototypeTrainer(make_env, episodes=1, ppo_epochs=1, seed=7)
    trainer_b = MAPPOPrototypeTrainer(make_env, episodes=1, ppo_epochs=1, seed=7)

    first_a = next(trainer_a.model.parameters()).detach().cpu()
    first_b = next(trainer_b.model.parameters()).detach().cpu()

    assert torch.equal(first_a, first_b)
