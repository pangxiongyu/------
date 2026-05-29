#!/usr/bin/env python3
"""
Minimal example for path-planning teammates.

Run this file from the extracted handoff package root:

    python examples/read_handoff_data.py

It demonstrates how to:
1. Read the weather cost map.
2. Select one time slice and one height layer.
3. Read UAV dynamic profiles.
4. Combine weather cost and UAV health into a simple assignment score.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WEATHER_SAMPLE = ROOT / "data" / "weather_cost_map" / "weather_cost_map_sample_24h.csv"
UAV_PROFILE = ROOT / "data" / "uav_profiles" / "torch_mamba_uav_dynamic_profiles.csv"


def main() -> None:
    weather = pd.read_csv(WEATHER_SAMPLE)
    profiles = pd.read_csv(UAV_PROFILE)

    print("weather rows:", len(weather))
    print("profile rows:", len(profiles))

    # Example: choose the first timestamp and 10m height layer.
    selected_time = weather["time"].iloc[0]
    layer = weather[(weather["time"] == selected_time) & (weather["height_m"] == 10)]
    print("selected weather layer:", selected_time, "height=10m", "rows=", len(layer))

    # Example weather cost at a candidate grid point.
    candidate = layer.iloc[len(layer) // 2]
    weather_cost = float(candidate["cost"])
    print("candidate weather cost:", weather_cost)

    # Example: choose the latest low-risk or medium-risk profile window.
    available = profiles[profiles["dynamic_risk_level"].isin(["low", "medium"])].copy()
    available["assignment_score"] = available["dynamic_health_score"] - 20.0 * weather_cost
    best = available.sort_values("assignment_score", ascending=False).iloc[0]

    print("best profile candidate:")
    print(
        {
            "flight_id": best["flight_id"],
            "route": best["route"],
            "dynamic_health_score": round(float(best["dynamic_health_score"]), 2),
            "dynamic_risk_level": best["dynamic_risk_level"],
            "assignment_score": round(float(best["assignment_score"]), 2),
        }
    )


if __name__ == "__main__":
    main()
