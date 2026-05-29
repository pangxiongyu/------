from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_io.scenario_loader import build_scenario
from src.planning.weather_grid_path import WeatherGridPathPlanner


def main() -> None:
    scenario = build_scenario(ROOT / "configs" / "default.yaml")
    start = scenario.uavs[0]
    goal = scenario.tasks[-1]
    planner = WeatherGridPathPlanner(
        scenario.weather_map,
        time=scenario.time,
        height_m=scenario.height_m,
        weather_weight=float(scenario.config.get("baseline", {}).get("weather_grid_weight", 20.0)),
    )
    result = planner.plan(
        start_lat=start.current_lat,
        start_lon=start.current_lon,
        goal_lat=goal.target_lat,
        goal_lon=goal.target_lon,
    )
    print("weather-aware grid path")
    print(
        {
            "start_uav": start.uav_id,
            "goal_task": goal.task_id,
            "waypoint_count": len(result.waypoints),
            "distance_km": round(result.distance_km, 3),
            "weather_cost_sum": round(result.weather_cost_sum, 3),
            "total_cost": round(result.total_cost, 3),
            "visited_count": result.visited_count,
        }
    )
    print("first_waypoints:", result.waypoints[:5])


if __name__ == "__main__":
    main()

