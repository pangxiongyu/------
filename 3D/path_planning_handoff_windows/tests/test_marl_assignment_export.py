from __future__ import annotations

import pandas as pd

from src.core.schemas import TaskState, UavProfile, UavState
from src.data_io.scenario_loader import PlanningScenario
from src.data_io.weather_loader import WeatherMap
from src.eval.scenario_eval import run_marl_greedy_evaluation


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


def test_run_marl_greedy_evaluation_exports_route_plans() -> None:
    rows = []
    for height in [10.0, 100.0]:
        for lat in [0.0, 1.0]:
            for lon in [0.0, 1.0]:
                rows.append(
                    {
                        "time": "t0",
                        "latitude": lat,
                        "longitude": lon,
                        "height_m": height,
                        "cost": 0.1,
                        "wind_speed": 0.0,
                        "wind_direction": 0.0,
                        "temperature_2m": 20.0,
                        "relative_humidity_2m": 50.0,
                        "weather_code": 0.0,
                    }
                )
    scenario = PlanningScenario(
        weather_map=WeatherMap(pd.DataFrame(rows)),
        profile_store=None,  # type: ignore[arg-type]
        uavs=[UavState("U1", 0.0, 0.0, 10.0, 500.0, make_profile())],
        tasks=[TaskState("T1", 1.0, 1.0, 100.0, payload_g=100.0)],
        time="t0",
        height_m=10.0,
        config={
            "baseline": {"weather_grid_weight": 20.0},
            "marl": {
                "max_steps": 1,
                "use_height_actions": False,
                "use_weather_grid_paths": False,
                "route_strategies": ["weather_3d"],
            },
        },
    )

    evaluation = run_marl_greedy_evaluation(scenario)

    assert evaluation.metrics["weather_3d_action_count"] == 1.0
    assert len(evaluation.assignment_result.assignments) == 1
    route = evaluation.assignment_result.assignments[0]
    assert route.metadata["route_strategy"] == "weather_3d"
    assert route.waypoints[0] == (0.0, 0.0, 10.0)
    assert route.waypoints[-1] == (1.0, 1.0, 100.0)
