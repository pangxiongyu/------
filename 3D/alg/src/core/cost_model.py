from __future__ import annotations

from src.core.geo_utils import haversine_distance_km
from src.core.schemas import TaskState, UavProfile, UavState, WeatherCell


RISK_PENALTIES = {
    "low": 0.0,
    "medium": 15.0,
    "high": 100.0,
}


def normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def risk_penalty(risk_level: str) -> float:
    return RISK_PENALTIES.get(str(risk_level).lower(), 50.0)


def energy_pressure(
    profile: UavProfile,
    current_scale: tuple[float, float] = (0.0, 35.0),
    voltage_scale: tuple[float, float] = (0.0, 1.5),
) -> float:
    current_term = normalize(profile.pred_avg_current_a, *current_scale)
    voltage_term = normalize(profile.pred_voltage_drop_v, *voltage_scale)
    return current_term + voltage_term


def health_loss_cost(profile: UavProfile) -> float:
    return max(0.0, 100.0 - profile.dynamic_health_score) / 100.0


def distance_cost_km(uav: UavState, task: TaskState) -> float:
    return haversine_distance_km(
        uav.current_lat,
        uav.current_lon,
        task.target_lat,
        task.target_lon,
    )


def path_cost(
    distance_km: float,
    weather_cost: float,
    altitude_change_m: float,
    profile: UavProfile,
    alpha: float = 1.0,
    beta: float = 0.3,
    gamma: float = 0.5,
    delta: float = 0.5,
) -> float:
    altitude_term = normalize(abs(altitude_change_m), 0.0, 120.0)
    return (
        distance_km
        + alpha * weather_cost
        + beta * altitude_term
        + gamma * health_loss_cost(profile)
        + delta * energy_pressure(profile)
    )


def assignment_score(
    uav: UavState,
    task: TaskState,
    weather: WeatherCell,
    max_distance_km: float = 1500.0,
    max_payload_g: float = 1000.0,
) -> float:
    distance_km = distance_cost_km(uav, task)
    normalized_distance = normalize(distance_km, 0.0, max_distance_km)
    normalized_payload = normalize(task.payload_g, 0.0, max_payload_g)
    return (
        uav.profile.dynamic_health_score
        - 20.0 * weather.cost
        - 10.0 * normalized_distance
        - 10.0 * normalized_payload
        - risk_penalty(uav.profile.dynamic_risk_level)
    )

