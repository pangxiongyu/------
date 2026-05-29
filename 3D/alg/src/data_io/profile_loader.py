from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.core.schemas import UavProfile


PROFILE_COLUMNS = [
    "flight_id",
    "route",
    "payload_g",
    "target_altitude_m",
    "window_start_s",
    "window_end_s",
    "pred_voltage_drop_v",
    "pred_avg_current_a",
    "pred_stability_risk",
    "pred_stability_pressure",
    "dynamic_health_score",
    "dynamic_risk_level",
]

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass
class DynamicProfileStore:
    frame: pd.DataFrame

    @classmethod
    def from_csv(cls, path: str | Path) -> "DynamicProfileStore":
        frame = pd.read_csv(path)
        missing = sorted(set(PROFILE_COLUMNS) - set(frame.columns))
        if missing:
            raise ValueError(f"Dynamic profile file is missing columns: {missing}")
        return cls(frame.copy())

    def select_available(self, max_risk: str = "medium") -> pd.DataFrame:
        max_rank = RISK_ORDER.get(max_risk, 1)
        ranks = self.frame["dynamic_risk_level"].map(lambda value: RISK_ORDER.get(value, 3))
        return self.frame[ranks <= max_rank].copy()

    def best_profiles(self, count: int | None = None, max_risk: str = "medium") -> list[UavProfile]:
        available = self.select_available(max_risk=max_risk)
        available = available.sort_values(
            ["dynamic_health_score", "window_end_s"],
            ascending=[False, False],
        )
        if count is not None:
            available = available.head(count)
        return [row_to_uav_profile(row) for _, row in available.iterrows()]

    def latest_profile_by_flight(self, flight_id: int) -> UavProfile:
        selected = self.frame[self.frame["flight_id"] == flight_id]
        if selected.empty:
            raise KeyError(f"Unknown flight_id: {flight_id}")
        row = selected.sort_values("window_end_s", ascending=False).iloc[0]
        return row_to_uav_profile(row)

    def profile_features(self, profile: UavProfile) -> list[float]:
        risk_rank = float(RISK_ORDER.get(profile.dynamic_risk_level, 3))
        return [
            profile.dynamic_health_score / 100.0,
            risk_rank / 2.0,
            profile.pred_avg_current_a,
            profile.pred_voltage_drop_v,
            profile.pred_stability_risk,
        ]


def row_to_uav_profile(row: pd.Series) -> UavProfile:
    return UavProfile(
        flight_id=int(row["flight_id"]),
        route=str(row["route"]),
        payload_g=float(row["payload_g"]),
        target_altitude_m=float(row["target_altitude_m"]),
        window_start_s=float(row["window_start_s"]),
        window_end_s=float(row["window_end_s"]),
        pred_voltage_drop_v=float(row["pred_voltage_drop_v"]),
        pred_avg_current_a=float(row["pred_avg_current_a"]),
        pred_stability_risk=float(row["pred_stability_risk"]),
        pred_stability_pressure=float(row["pred_stability_pressure"]),
        dynamic_health_score=float(row["dynamic_health_score"]),
        dynamic_risk_level=str(row["dynamic_risk_level"]),
    )


def load_dynamic_profiles(path: str | Path) -> DynamicProfileStore:
    return DynamicProfileStore.from_csv(path)

