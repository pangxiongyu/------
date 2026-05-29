#!/usr/bin/env python3
"""
Build a Mamba-lite dynamic UAV profile from flight telemetry.

Why "Mamba-lite":
    The local environment may not have PyTorch or mamba-ssm installed. This
    script implements the key engineering idea we need for the project first:
    sequence modeling with a selective state-space scan.

    Each time window is encoded by a gated state update:

        h_t = gate(x_t) * (A * h_{t-1} + B * x_t)

    Then a ridge-regression prediction head estimates short-horizon voltage
    drop, current pressure, and stability risk. This gives us a usable dynamic
    profile file now, while keeping a clean upgrade path to real Mamba later.
"""

from __future__ import annotations

import csv
import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "UAV_datas"
FLIGHTS_DIR = DATA_DIR / "flights"
PARAMETERS_FILE = DATA_DIR / "parameters.csv"
OUTPUT_DIR = BASE_DIR / "generated_uav_profiles"
OUTPUT_FILE = OUTPUT_DIR / "mamba_uav_dynamic_profiles.csv"
METRICS_FILE = OUTPUT_DIR / "mamba_lite_metrics.json"

WINDOW_SIZE = 60
PREDICTION_HORIZON = 30
STRIDE = 30
HIDDEN_DIM = 32
RIDGE_LAMBDA = 1e-2
RANDOM_SEED = 42

FEATURE_COLUMNS = [
    "wind_speed",
    "battery_voltage",
    "battery_current",
    "velocity_x",
    "velocity_y",
    "velocity_z",
    "angular_x",
    "angular_y",
    "angular_z",
    "linear_acceleration_x",
    "linear_acceleration_y",
    "linear_acceleration_z",
    "position_z",
]

TARGET_COLUMNS = [
    "future_voltage_drop_v",
    "future_avg_current_a",
    "future_stability_risk",
]


@dataclass
class WindowSample:
    flight_id: str
    route: str
    payload_g: str
    target_altitude_m: str
    start_time_s: float
    end_time_s: float
    features: np.ndarray
    targets: np.ndarray


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def load_parameters() -> dict[str, dict[str, str]]:
    with PARAMETERS_FILE.open("r", encoding="utf-8", newline="") as file:
        return {row["flight"]: row for row in csv.DictReader(file)}


def read_flight(file_path: Path) -> dict[str, np.ndarray]:
    columns: dict[str, list[float]] = {"time": []}
    for col in FEATURE_COLUMNS:
        columns[col] = []

    with file_path.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            columns["time"].append(to_float(row["time"]))
            for col in FEATURE_COLUMNS:
                columns[col].append(to_float(row[col]))

    return {key: np.asarray(values, dtype=np.float64) for key, values in columns.items()}


def compute_stability_risk(window: dict[str, np.ndarray], start: int, end: int) -> float:
    vx = window["velocity_x"][start:end]
    vy = window["velocity_y"][start:end]
    vz = window["velocity_z"][start:end]
    ax = window["angular_x"][start:end]
    ay = window["angular_y"][start:end]
    az = window["angular_z"][start:end]
    lx = window["linear_acceleration_x"][start:end]
    ly = window["linear_acceleration_y"][start:end]
    lz = window["linear_acceleration_z"][start:end]

    speed = np.sqrt(vx * vx + vy * vy + vz * vz)
    angular = np.sqrt(ax * ax + ay * ay + az * az)
    acceleration = np.sqrt(lx * lx + ly * ly + lz * lz)

    speed_std = float(np.std(speed))
    vertical_std = float(np.std(vz))
    angular_mean = float(np.mean(angular))
    acceleration_std = float(np.std(acceleration))

    raw = 0.45 * speed_std + 0.25 * vertical_std + 18.0 * angular_mean + 0.35 * acceleration_std
    return float(np.clip(raw / 12.0, 0.0, 1.0))


def build_samples() -> list[WindowSample]:
    parameters = load_parameters()
    samples: list[WindowSample] = []

    for file_path in sorted(FLIGHTS_DIR.glob("*.csv"), key=lambda p: int(p.stem)):
        flight_id = file_path.stem
        params = parameters.get(flight_id, {})
        data = read_flight(file_path)
        n_rows = len(data["time"])
        max_start = n_rows - WINDOW_SIZE - PREDICTION_HORIZON
        if max_start <= 0:
            continue

        feature_matrix = np.column_stack([data[col] for col in FEATURE_COLUMNS])
        for start in range(0, max_start + 1, STRIDE):
            mid = start + WINDOW_SIZE
            end = mid + PREDICTION_HORIZON
            x = feature_matrix[start:mid]

            current_voltage = data["battery_voltage"][mid - 1]
            future_voltage = data["battery_voltage"][end - 1]
            future_voltage_drop = max(0.0, float(current_voltage - future_voltage))
            future_current = np.maximum(data["battery_current"][mid:end], 0.0)
            future_avg_current = float(np.mean(future_current))
            future_stability_risk = compute_stability_risk(data, mid, end)

            samples.append(
                WindowSample(
                    flight_id=flight_id,
                    route=params.get("route", ""),
                    payload_g=params.get("payload", ""),
                    target_altitude_m=params.get("altitude", ""),
                    start_time_s=float(data["time"][start]),
                    end_time_s=float(data["time"][mid - 1]),
                    features=x,
                    targets=np.asarray(
                        [future_voltage_drop, future_avg_current, future_stability_risk],
                        dtype=np.float64,
                    ),
                )
            )
    return samples


def train_test_split(samples: list[WindowSample]) -> tuple[list[WindowSample], list[WindowSample]]:
    # Split by flight ID to avoid leakage between windows from the same flight.
    flight_ids = sorted({sample.flight_id for sample in samples}, key=int)
    rng = np.random.default_rng(RANDOM_SEED)
    shuffled = np.asarray(flight_ids)
    rng.shuffle(shuffled)
    test_count = max(1, int(0.2 * len(shuffled)))
    test_ids = set(shuffled[:test_count])

    train = [sample for sample in samples if sample.flight_id not in test_ids]
    test = [sample for sample in samples if sample.flight_id in test_ids]
    return train, test


def fit_standardizer(train_samples: list[WindowSample]) -> tuple[np.ndarray, np.ndarray]:
    stacked = np.concatenate([sample.features for sample in train_samples], axis=0)
    mean = stacked.mean(axis=0)
    std = stacked.std(axis=0)
    std[std < 1e-8] = 1.0
    return mean, std


class MambaLiteEncoder:
    def __init__(self, input_dim: int, hidden_dim: int, seed: int = RANDOM_SEED) -> None:
        rng = np.random.default_rng(seed)
        self.a = rng.uniform(0.70, 0.98, size=(hidden_dim,))
        self.b = rng.normal(0.0, 0.25, size=(input_dim, hidden_dim))
        self.gate_w = rng.normal(0.0, 0.25, size=(input_dim, hidden_dim))
        self.gate_b = rng.normal(0.0, 0.05, size=(hidden_dim,))

    def encode_one(self, sequence: np.ndarray) -> np.ndarray:
        h = np.zeros((self.a.shape[0],), dtype=np.float64)
        states = []
        for x_t in sequence:
            gate = sigmoid(x_t @ self.gate_w + self.gate_b)
            candidate = self.a * h + x_t @ self.b
            h = gate * np.tanh(candidate) + (1.0 - gate) * h
            states.append(h.copy())

        state_matrix = np.asarray(states)
        return np.concatenate(
            [
                state_matrix[-1],
                state_matrix.mean(axis=0),
                state_matrix.std(axis=0),
                sequence.mean(axis=0),
                sequence.std(axis=0),
            ]
        )

    def encode_many(self, samples: list[WindowSample], mean: np.ndarray, std: np.ndarray) -> np.ndarray:
        encoded = []
        for sample in samples:
            normalized = (sample.features - mean) / std
            encoded.append(self.encode_one(normalized))
        return np.vstack(encoded)


def fit_target_standardizer(y_train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = y_train.mean(axis=0)
    std = y_train.std(axis=0)
    std[std < 1e-8] = 1.0
    return mean, std


def standardize_matrix(
    train_matrix: np.ndarray,
    *other_matrices: np.ndarray,
) -> tuple[np.ndarray, ...]:
    mean = train_matrix.mean(axis=0)
    std = train_matrix.std(axis=0)
    std[std < 1e-8] = 1.0
    standardized = [(train_matrix - mean) / std]
    standardized.extend((matrix - mean) / std for matrix in other_matrices)
    return tuple(standardized)


def ridge_fit(x: np.ndarray, y: np.ndarray, lambda_value: float) -> np.ndarray:
    x_aug = np.column_stack([np.ones((x.shape[0],)), x])
    identity = np.eye(x_aug.shape[1])
    identity[0, 0] = 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.linalg.solve(x_aug.T @ x_aug + lambda_value * identity, x_aug.T @ y)


def ridge_predict(x: np.ndarray, weights: np.ndarray) -> np.ndarray:
    x_aug = np.column_stack([np.ones((x.shape[0],)), x])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return x_aug @ weights


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}
    for idx, name in enumerate(TARGET_COLUMNS):
        err = y_pred[:, idx] - y_true[:, idx]
        mae = float(np.mean(np.abs(err)))
        rmse = float(np.sqrt(np.mean(err * err)))
        denominator = float(np.sum((y_true[:, idx] - y_true[:, idx].mean()) ** 2))
        r2 = 1.0 - float(np.sum(err * err)) / denominator if denominator > 1e-12 else 0.0
        metrics[name] = {"mae": mae, "rmse": rmse, "r2": r2}
    return metrics


def dynamic_health(predictions: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    voltage_drop = np.clip(predictions[:, 0], 0.0, None)
    avg_current = np.clip(predictions[:, 1], 0.0, None)
    stability_risk = np.clip(predictions[:, 2], 0.0, 1.0)

    voltage_pressure = np.clip(voltage_drop / 1.2, 0.0, 1.0) * 100.0
    current_pressure = np.clip(avg_current / 45.0, 0.0, 1.0) * 100.0
    stability_pressure = stability_risk * 100.0
    health = 100.0 - (0.35 * voltage_pressure + 0.35 * current_pressure + 0.30 * stability_pressure)
    health = np.clip(health, 0.0, 100.0)
    risk = np.where(health >= 75.0, "low", np.where(health >= 55.0, "medium", "high"))
    return health, stability_pressure, risk


def write_dynamic_profiles(
    samples: list[WindowSample],
    predictions: np.ndarray,
) -> None:
    health, stability_pressure, risk = dynamic_health(predictions)
    fieldnames = [
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

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for idx, sample in enumerate(samples):
            writer.writerow(
                {
                    "flight_id": sample.flight_id,
                    "route": sample.route,
                    "payload_g": sample.payload_g,
                    "target_altitude_m": sample.target_altitude_m,
                    "window_start_s": f"{sample.start_time_s:.2f}",
                    "window_end_s": f"{sample.end_time_s:.2f}",
                    "pred_voltage_drop_v": f"{max(0.0, predictions[idx, 0]):.5f}",
                    "pred_avg_current_a": f"{max(0.0, predictions[idx, 1]):.5f}",
                    "pred_stability_risk": f"{np.clip(predictions[idx, 2], 0.0, 1.0):.5f}",
                    "pred_stability_pressure": f"{stability_pressure[idx]:.2f}",
                    "dynamic_health_score": f"{health[idx]:.2f}",
                    "dynamic_risk_level": str(risk[idx]),
                }
            )


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    samples = build_samples()
    train_samples, test_samples = train_test_split(samples)
    feature_mean, feature_std = fit_standardizer(train_samples)

    encoder = MambaLiteEncoder(input_dim=len(FEATURE_COLUMNS), hidden_dim=HIDDEN_DIM)
    x_train = encoder.encode_many(train_samples, feature_mean, feature_std)
    x_test = encoder.encode_many(test_samples, feature_mean, feature_std)
    x_all = encoder.encode_many(samples, feature_mean, feature_std)
    x_train, x_test, x_all = standardize_matrix(x_train, x_test, x_all)

    y_train = np.vstack([sample.targets for sample in train_samples])
    y_test = np.vstack([sample.targets for sample in test_samples])
    target_mean, target_std = fit_target_standardizer(y_train)
    y_train_scaled = (y_train - target_mean) / target_std

    weights = ridge_fit(x_train, y_train_scaled, RIDGE_LAMBDA)
    test_pred_scaled = ridge_predict(x_test, weights)
    test_pred = test_pred_scaled * target_std + target_mean

    all_pred_scaled = ridge_predict(x_all, weights)
    all_pred = all_pred_scaled * target_std + target_mean
    all_pred[:, 0] = np.clip(all_pred[:, 0], 0.0, None)
    all_pred[:, 1] = np.clip(all_pred[:, 1], 0.0, None)
    all_pred[:, 2] = np.clip(all_pred[:, 2], 0.0, 1.0)

    write_dynamic_profiles(samples, all_pred)

    metrics = {
        "model": "mamba_lite_selective_state_space_plus_ridge",
        "window_size": WINDOW_SIZE,
        "prediction_horizon": PREDICTION_HORIZON,
        "stride": STRIDE,
        "hidden_dim": HIDDEN_DIM,
        "sample_count": len(samples),
        "train_windows": len(train_samples),
        "test_windows": len(test_samples),
        "target_columns": TARGET_COLUMNS,
        "feature_columns": FEATURE_COLUMNS,
        "test_metrics": regression_metrics(y_test, test_pred),
        "note": "This is an interpretable prototype. Replace with PyTorch mamba-ssm later if needed.",
    }
    METRICS_FILE.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Generated metrics: {METRICS_FILE}")
    print(f"Windows: {len(samples)} train={len(train_samples)} test={len(test_samples)}")


if __name__ == "__main__":
    main()
