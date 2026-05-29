from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


Waypoint = tuple[float, float, float]


@dataclass(frozen=True)
class WeatherCell:
    time: str
    latitude: float
    longitude: float
    height_m: float
    cost: float
    wind_speed: float = 0.0
    wind_direction: float = 0.0
    temperature_2m: float | None = None
    relative_humidity_2m: float | None = None
    weather_code: float | None = None


@dataclass(frozen=True)
class UavProfile:
    flight_id: int
    route: str
    payload_g: float
    target_altitude_m: float
    window_start_s: float
    window_end_s: float
    pred_voltage_drop_v: float
    pred_avg_current_a: float
    pred_stability_risk: float
    pred_stability_pressure: float
    dynamic_health_score: float
    dynamic_risk_level: str


@dataclass
class UavState:
    uav_id: str
    current_lat: float
    current_lon: float
    current_height_m: float
    payload_capacity_g: float
    profile: UavProfile
    status: str = "idle"
    assigned_task_id: str | None = None


@dataclass
class TaskState:
    task_id: str
    target_lat: float
    target_lon: float
    target_height_m: float
    payload_g: float = 0.0
    deadline_s: float | None = None
    priority: float = 1.0
    status: str = "pending"


@dataclass(frozen=True)
class CandidateEvaluation:
    uav_id: str
    task_id: str
    score: float
    path_cost: float
    distance_km: float
    weather_cost: float
    risk_penalty: float
    energy_pressure: float
    reason: str = ""


@dataclass
class RoutePlan:
    uav_id: str
    task_id: str
    waypoints: list[Waypoint]
    total_distance_km: float
    total_cost: float
    weather_cost: float
    profile_cost: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssignmentResult:
    assignments: list[RoutePlan]
    rejected_tasks: list[str]
    total_score: float
    total_cost: float
    metadata: dict[str, Any] = field(default_factory=dict)

