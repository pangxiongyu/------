#!/usr/bin/env python3
"""
Generate a first-version UAV capability profile from UAV_datas.

This version is intentionally interpretable. It does not train Mamba yet.
Instead, it summarizes each flight into energy, wind, stability, and health
features that can be consumed by path planning and visualization modules.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean, pstdev


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "UAV_datas"
FLIGHTS_DIR = DATA_DIR / "flights"
PARAMETERS_FILE = DATA_DIR / "parameters.csv"
OUTPUT_DIR = BASE_DIR / "generated_uav_profiles"
OUTPUT_FILE = OUTPUT_DIR / "uav_profiles.csv"


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_parameters() -> dict[str, dict[str, str]]:
    with PARAMETERS_FILE.open("r", encoding="utf-8", newline="") as file:
        return {row["flight"]: row for row in csv.DictReader(file)}


def positive_current(value: float) -> float:
    # Small negative readings may appear around idle/charging sensor offsets.
    return max(0.0, value)


def trapezoid_energy_wh(times: list[float], voltages: list[float], currents: list[float]) -> float:
    if len(times) < 2:
        return 0.0
    energy_ws = 0.0
    for idx in range(1, len(times)):
        dt = max(0.0, times[idx] - times[idx - 1])
        p0 = voltages[idx - 1] * positive_current(currents[idx - 1])
        p1 = voltages[idx] * positive_current(currents[idx])
        energy_ws += (p0 + p1) * 0.5 * dt
    return energy_ws / 3600.0


def classify_risk(health_score: float) -> str:
    if health_score >= 75:
        return "low"
    if health_score >= 55:
        return "medium"
    return "high"


def classify_capacity(health_score: float, energy_efficiency_score: float) -> str:
    if health_score >= 80 and energy_efficiency_score >= 75:
        return "A"
    if health_score >= 65:
        return "B"
    if health_score >= 50:
        return "C"
    return "D"


def normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def summarize_flight(file_path: Path, params: dict[str, str]) -> dict[str, str]:
    times: list[float] = []
    wind_speeds: list[float] = []
    voltages: list[float] = []
    currents: list[float] = []
    velocity_magnitudes: list[float] = []
    vertical_velocities: list[float] = []
    angular_magnitudes: list[float] = []
    acceleration_magnitudes: list[float] = []
    positions_z: list[float] = []

    with file_path.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            time = to_float(row["time"])
            wind_speed = to_float(row["wind_speed"])
            voltage = to_float(row["battery_voltage"])
            current = to_float(row["battery_current"])
            velocity_x = to_float(row["velocity_x"])
            velocity_y = to_float(row["velocity_y"])
            velocity_z = to_float(row["velocity_z"])
            angular_x = to_float(row["angular_x"])
            angular_y = to_float(row["angular_y"])
            angular_z = to_float(row["angular_z"])
            acceleration_x = to_float(row["linear_acceleration_x"])
            acceleration_y = to_float(row["linear_acceleration_y"])
            acceleration_z = to_float(row["linear_acceleration_z"])

            times.append(time)
            wind_speeds.append(wind_speed)
            voltages.append(voltage)
            currents.append(current)
            positions_z.append(to_float(row["position_z"]))
            velocity_magnitudes.append(math.sqrt(velocity_x**2 + velocity_y**2 + velocity_z**2))
            vertical_velocities.append(velocity_z)
            angular_magnitudes.append(math.sqrt(angular_x**2 + angular_y**2 + angular_z**2))
            acceleration_magnitudes.append(
                math.sqrt(acceleration_x**2 + acceleration_y**2 + acceleration_z**2)
            )

    duration_s = max(times) - min(times) if times else 0.0
    energy_wh = trapezoid_energy_wh(times, voltages, currents)
    distance_proxy_m = sum(velocity_magnitudes[idx] * max(0.0, times[idx] - times[idx - 1]) for idx in range(1, len(times)))
    energy_per_min = energy_wh / (duration_s / 60.0) if duration_s > 0 else 0.0
    energy_per_meter = energy_wh / distance_proxy_m if distance_proxy_m > 0 else 0.0

    avg_wind = mean(wind_speeds) if wind_speeds else 0.0
    max_wind = max(wind_speeds) if wind_speeds else 0.0
    avg_current = mean([positive_current(v) for v in currents]) if currents else 0.0
    max_current = max([positive_current(v) for v in currents]) if currents else 0.0
    start_voltage = voltages[0] if voltages else 0.0
    end_voltage = voltages[-1] if voltages else 0.0
    min_voltage = min(voltages) if voltages else 0.0
    voltage_drop = max(0.0, start_voltage - end_voltage)

    speed_std = pstdev(velocity_magnitudes) if len(velocity_magnitudes) > 1 else 0.0
    vertical_speed_std = pstdev(vertical_velocities) if len(vertical_velocities) > 1 else 0.0
    angular_mean = mean(angular_magnitudes) if angular_magnitudes else 0.0
    acceleration_std = pstdev(acceleration_magnitudes) if len(acceleration_magnitudes) > 1 else 0.0
    altitude_std = pstdev(positions_z) if len(positions_z) > 1 else 0.0

    wind_pressure = 100.0 * normalize(0.65 * avg_wind + 0.35 * max_wind, 0.0, 16.0)
    energy_pressure = 100.0 * normalize(energy_per_min, 0.0, 12.0)
    current_pressure = 100.0 * normalize(max_current, 0.0, 60.0)
    stability_pressure = 100.0 * normalize(
        0.45 * speed_std + 0.25 * vertical_speed_std + 18.0 * angular_mean + 0.35 * acceleration_std,
        0.0,
        12.0,
    )
    voltage_pressure = 100.0 * normalize(voltage_drop, 0.0, 4.5)

    health_score = 100.0 - (
        0.25 * wind_pressure
        + 0.25 * energy_pressure
        + 0.18 * current_pressure
        + 0.22 * stability_pressure
        + 0.10 * voltage_pressure
    )
    health_score = max(0.0, min(100.0, health_score))
    energy_efficiency_score = max(0.0, min(100.0, 100.0 - energy_pressure))

    flight_id = file_path.stem
    return {
        "flight_id": flight_id,
        "route": params.get("route", ""),
        "target_speed_mps": params.get("speed", ""),
        "payload_g": params.get("payload", ""),
        "target_altitude_m": params.get("altitude", ""),
        "date": params.get("date", ""),
        "local_time": params.get("local_time", ""),
        "duration_s": f"{duration_s:.2f}",
        "sample_count": str(len(times)),
        "avg_wind_speed_mps": f"{avg_wind:.4f}",
        "max_wind_speed_mps": f"{max_wind:.4f}",
        "avg_current_a": f"{avg_current:.4f}",
        "max_current_a": f"{max_current:.4f}",
        "start_voltage_v": f"{start_voltage:.4f}",
        "end_voltage_v": f"{end_voltage:.4f}",
        "min_voltage_v": f"{min_voltage:.4f}",
        "voltage_drop_v": f"{voltage_drop:.4f}",
        "energy_wh": f"{energy_wh:.4f}",
        "energy_per_min_wh": f"{energy_per_min:.4f}",
        "energy_per_meter_wh": f"{energy_per_meter:.6f}",
        "speed_std": f"{speed_std:.4f}",
        "vertical_speed_std": f"{vertical_speed_std:.4f}",
        "angular_mean": f"{angular_mean:.6f}",
        "acceleration_std": f"{acceleration_std:.4f}",
        "altitude_std_m": f"{altitude_std:.4f}",
        "wind_pressure": f"{wind_pressure:.2f}",
        "energy_pressure": f"{energy_pressure:.2f}",
        "stability_pressure": f"{stability_pressure:.2f}",
        "health_score": f"{health_score:.2f}",
        "energy_efficiency_score": f"{energy_efficiency_score:.2f}",
        "capacity_grade": classify_capacity(health_score, energy_efficiency_score),
        "risk_level": classify_risk(health_score),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    parameters = load_parameters()
    rows: list[dict[str, str]] = []

    for file_path in sorted(FLIGHTS_DIR.glob("*.csv"), key=lambda p: int(p.stem)):
        params = parameters.get(file_path.stem, {})
        rows.append(summarize_flight(file_path, params))

    fieldnames = list(rows[0].keys()) if rows else []
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Flights profiled: {len(rows)}")


if __name__ == "__main__":
    main()
