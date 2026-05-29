#!/usr/bin/env python3
"""
PyTorch Mamba-style dynamic UAV profile model.

This script runs in the conda environment `py311` where PyTorch is available.
It replaces the previous NumPy-only Mamba-lite regression head with a trainable
sequence model implemented in PyTorch.

It does not require the external `mamba-ssm` package. The model uses a compact
selective state-space block inspired by Mamba's gated recurrent scan, which is
enough for the project prototype and keeps installation simple on macOS.
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "UAV_datas"
FLIGHTS_DIR = DATA_DIR / "flights"
PARAMETERS_FILE = DATA_DIR / "parameters.csv"
OUTPUT_DIR = BASE_DIR / "generated_uav_profiles"
OUTPUT_FILE = OUTPUT_DIR / "torch_mamba_uav_dynamic_profiles.csv"
METRICS_FILE = OUTPUT_DIR / "torch_mamba_metrics.json"
MODEL_FILE = OUTPUT_DIR / "torch_mamba_uav_profile_model.pt"

WINDOW_SIZE = 60
PREDICTION_HORIZON = 30
STRIDE = 30
RANDOM_SEED = 42

BATCH_SIZE = 128
EPOCHS = 35
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
MODEL_DIM = 64
MODEL_DEPTH = 2
DROPOUT = 0.10

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
class WindowMeta:
    flight_id: str
    route: str
    payload_g: str
    target_altitude_m: str
    start_time_s: float
    end_time_s: float


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_parameters() -> dict[str, dict[str, str]]:
    with PARAMETERS_FILE.open("r", encoding="utf-8", newline="") as file:
        return {row["flight"]: row for row in csv.DictReader(file)}


def read_flight(file_path: Path) -> dict[str, np.ndarray]:
    columns: dict[str, list[float]] = {"time": []}
    for column in FEATURE_COLUMNS:
        columns[column] = []

    with file_path.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            columns["time"].append(to_float(row["time"]))
            for column in FEATURE_COLUMNS:
                columns[column].append(to_float(row[column]))

    return {key: np.asarray(values, dtype=np.float32) for key, values in columns.items()}


def compute_stability_risk(data: dict[str, np.ndarray], start: int, end: int) -> float:
    vx = data["velocity_x"][start:end]
    vy = data["velocity_y"][start:end]
    vz = data["velocity_z"][start:end]
    ax = data["angular_x"][start:end]
    ay = data["angular_y"][start:end]
    az = data["angular_z"][start:end]
    lx = data["linear_acceleration_x"][start:end]
    ly = data["linear_acceleration_y"][start:end]
    lz = data["linear_acceleration_z"][start:end]

    speed = np.sqrt(vx * vx + vy * vy + vz * vz)
    angular = np.sqrt(ax * ax + ay * ay + az * az)
    acceleration = np.sqrt(lx * lx + ly * ly + lz * lz)

    raw = (
        0.45 * float(np.std(speed))
        + 0.25 * float(np.std(vz))
        + 18.0 * float(np.mean(angular))
        + 0.35 * float(np.std(acceleration))
    )
    return float(np.clip(raw / 12.0, 0.0, 1.0))


def build_windows() -> tuple[np.ndarray, np.ndarray, list[WindowMeta]]:
    parameters = load_parameters()
    features: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    metadata: list[WindowMeta] = []

    for file_path in sorted(FLIGHTS_DIR.glob("*.csv"), key=lambda path: int(path.stem)):
        flight_id = file_path.stem
        params = parameters.get(flight_id, {})
        data = read_flight(file_path)
        n_rows = len(data["time"])
        max_start = n_rows - WINDOW_SIZE - PREDICTION_HORIZON
        if max_start <= 0:
            continue

        feature_matrix = np.column_stack([data[column] for column in FEATURE_COLUMNS]).astype(np.float32)
        for start in range(0, max_start + 1, STRIDE):
            mid = start + WINDOW_SIZE
            end = mid + PREDICTION_HORIZON

            current_voltage = float(data["battery_voltage"][mid - 1])
            future_voltage = float(data["battery_voltage"][end - 1])
            future_voltage_drop = max(0.0, current_voltage - future_voltage)
            future_current = np.maximum(data["battery_current"][mid:end], 0.0)
            future_avg_current = float(np.mean(future_current))
            future_stability_risk = compute_stability_risk(data, mid, end)

            features.append(feature_matrix[start:mid])
            targets.append(
                np.asarray(
                    [future_voltage_drop, future_avg_current, future_stability_risk],
                    dtype=np.float32,
                )
            )
            metadata.append(
                WindowMeta(
                    flight_id=flight_id,
                    route=params.get("route", ""),
                    payload_g=params.get("payload", ""),
                    target_altitude_m=params.get("altitude", ""),
                    start_time_s=float(data["time"][start]),
                    end_time_s=float(data["time"][mid - 1]),
                )
            )

    return np.stack(features), np.stack(targets), metadata


def split_by_flight(metadata: list[WindowMeta]) -> tuple[np.ndarray, np.ndarray]:
    flight_ids = sorted({item.flight_id for item in metadata}, key=int)
    rng = np.random.default_rng(RANDOM_SEED)
    shuffled = np.asarray(flight_ids)
    rng.shuffle(shuffled)
    test_count = max(1, int(0.2 * len(shuffled)))
    test_ids = set(shuffled[:test_count])

    train_indices = []
    test_indices = []
    for index, item in enumerate(metadata):
        if item.flight_id in test_ids:
            test_indices.append(index)
        else:
            train_indices.append(index)
    return np.asarray(train_indices), np.asarray(test_indices)


def fit_standardizer(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = values.mean(axis=tuple(range(values.ndim - 1)), keepdims=True)
    std = values.std(axis=tuple(range(values.ndim - 1)), keepdims=True)
    std[std < 1e-6] = 1.0
    return mean.astype(np.float32), std.astype(np.float32)


class WindowDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray, indices: np.ndarray) -> None:
        self.x = torch.from_numpy(x[indices]).float()
        self.y = torch.from_numpy(y[indices]).float()

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.x[index], self.y[index]


class SelectiveStateSpaceBlock(nn.Module):
    """Compact Mamba-style selective scan block."""

    def __init__(self, dim: int, dropout: float) -> None:
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.in_proj = nn.Linear(dim, dim)
        self.gate_proj = nn.Linear(dim, dim)
        self.out_proj = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(dropout)
        self.a_logit = nn.Parameter(torch.zeros(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        x = self.norm(x)
        batch_size, seq_len, dim = x.shape
        h = torch.zeros(batch_size, dim, device=x.device, dtype=x.dtype)
        a = torch.sigmoid(self.a_logit)
        outputs = []

        for step in range(seq_len):
            x_t = x[:, step, :]
            gate = torch.sigmoid(self.gate_proj(x_t))
            candidate = torch.tanh(a * h + self.in_proj(x_t))
            h = gate * candidate + (1.0 - gate) * h
            outputs.append(h)

        y = torch.stack(outputs, dim=1)
        y = self.out_proj(y)
        return residual + self.dropout(y)


class TorchMambaProfileModel(nn.Module):
    def __init__(self, input_dim: int, model_dim: int, depth: int, dropout: float) -> None:
        super().__init__()
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, model_dim),
            nn.GELU(),
            nn.LayerNorm(model_dim),
        )
        self.blocks = nn.ModuleList(
            [SelectiveStateSpaceBlock(model_dim, dropout=dropout) for _ in range(depth)]
        )
        self.head = nn.Sequential(
            nn.LayerNorm(model_dim * 2),
            nn.Linear(model_dim * 2, model_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(model_dim, len(TARGET_COLUMNS)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x)
        for block in self.blocks:
            x = block(x)
        pooled = torch.cat([x[:, -1, :], x.mean(dim=1)], dim=1)
        return self.head(pooled)


def choose_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    test_loader: DataLoader,
    target_mean: torch.Tensor,
    target_std: torch.Tensor,
    device: torch.device,
) -> dict[str, list[float]]:
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    loss_fn = nn.SmoothL1Loss()
    history = {"train_loss": [], "test_loss": []}

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_losses = []
        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)
            y_scaled = (y_batch - target_mean) / target_std

            optimizer.zero_grad(set_to_none=True)
            prediction = model(x_batch)
            loss = loss_fn(prediction, y_scaled)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))

        model.eval()
        test_losses = []
        with torch.no_grad():
            for x_batch, y_batch in test_loader:
                x_batch = x_batch.to(device)
                y_batch = y_batch.to(device)
                y_scaled = (y_batch - target_mean) / target_std
                prediction = model(x_batch)
                test_losses.append(float(loss_fn(prediction, y_scaled).detach().cpu()))

        history["train_loss"].append(float(np.mean(train_losses)))
        history["test_loss"].append(float(np.mean(test_losses)))
        if epoch == 1 or epoch % 5 == 0 or epoch == EPOCHS:
            print(
                f"epoch={epoch:02d} "
                f"train_loss={history['train_loss'][-1]:.5f} "
                f"test_loss={history['test_loss'][-1]:.5f}"
            )

    return history


def predict_all(
    model: nn.Module,
    x: np.ndarray,
    target_mean: np.ndarray,
    target_std: np.ndarray,
    device: torch.device,
) -> np.ndarray:
    dataset = torch.from_numpy(x).float()
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)
    predictions = []
    model.eval()
    mean_tensor = torch.from_numpy(target_mean).to(device)
    std_tensor = torch.from_numpy(target_std).to(device)

    with torch.no_grad():
        for x_batch in loader:
            x_batch = x_batch.to(device)
            pred_scaled = model(x_batch)
            pred = pred_scaled * std_tensor + mean_tensor
            predictions.append(pred.detach().cpu().numpy())

    prediction_array = np.concatenate(predictions, axis=0)
    prediction_array[:, 0] = np.clip(prediction_array[:, 0], 0.0, None)
    prediction_array[:, 1] = np.clip(prediction_array[:, 1], 0.0, None)
    prediction_array[:, 2] = np.clip(prediction_array[:, 2], 0.0, 1.0)
    return prediction_array


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}
    for index, name in enumerate(TARGET_COLUMNS):
        error = y_pred[:, index] - y_true[:, index]
        mae = float(np.mean(np.abs(error)))
        rmse = float(np.sqrt(np.mean(error * error)))
        denominator = float(np.sum((y_true[:, index] - y_true[:, index].mean()) ** 2))
        r2 = 1.0 - float(np.sum(error * error)) / denominator if denominator > 1e-12 else 0.0
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


def write_dynamic_profiles(metadata: list[WindowMeta], predictions: np.ndarray) -> None:
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
        for index, item in enumerate(metadata):
            writer.writerow(
                {
                    "flight_id": item.flight_id,
                    "route": item.route,
                    "payload_g": item.payload_g,
                    "target_altitude_m": item.target_altitude_m,
                    "window_start_s": f"{item.start_time_s:.2f}",
                    "window_end_s": f"{item.end_time_s:.2f}",
                    "pred_voltage_drop_v": f"{predictions[index, 0]:.5f}",
                    "pred_avg_current_a": f"{predictions[index, 1]:.5f}",
                    "pred_stability_risk": f"{predictions[index, 2]:.5f}",
                    "pred_stability_pressure": f"{stability_pressure[index]:.2f}",
                    "dynamic_health_score": f"{health[index]:.2f}",
                    "dynamic_risk_level": str(risk[index]),
                }
            )


def main() -> None:
    set_seed(RANDOM_SEED)
    OUTPUT_DIR.mkdir(exist_ok=True)

    x, y, metadata = build_windows()
    train_indices, test_indices = split_by_flight(metadata)

    feature_mean, feature_std = fit_standardizer(x[train_indices])
    target_mean = y[train_indices].mean(axis=0, keepdims=True).astype(np.float32)
    target_std = y[train_indices].std(axis=0, keepdims=True).astype(np.float32)
    target_std[target_std < 1e-6] = 1.0

    x_normalized = ((x - feature_mean) / feature_std).astype(np.float32)
    train_dataset = WindowDataset(x_normalized, y, train_indices)
    test_dataset = WindowDataset(x_normalized, y, test_indices)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    device = choose_device()
    print(f"device={device}")
    model = TorchMambaProfileModel(
        input_dim=len(FEATURE_COLUMNS),
        model_dim=MODEL_DIM,
        depth=MODEL_DEPTH,
        dropout=DROPOUT,
    ).to(device)

    target_mean_tensor = torch.from_numpy(target_mean).to(device)
    target_std_tensor = torch.from_numpy(target_std).to(device)
    history = train_model(model, train_loader, test_loader, target_mean_tensor, target_std_tensor, device)

    predictions = predict_all(model, x_normalized, target_mean, target_std, device)
    write_dynamic_profiles(metadata, predictions)

    test_predictions = predictions[test_indices]
    metrics = {
        "model": "torch_selective_state_space_mamba_style",
        "device": str(device),
        "window_size": WINDOW_SIZE,
        "prediction_horizon": PREDICTION_HORIZON,
        "stride": STRIDE,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "model_dim": MODEL_DIM,
        "model_depth": MODEL_DEPTH,
        "sample_count": int(len(metadata)),
        "train_windows": int(len(train_indices)),
        "test_windows": int(len(test_indices)),
        "target_columns": TARGET_COLUMNS,
        "feature_columns": FEATURE_COLUMNS,
        "test_metrics": regression_metrics(y[test_indices], test_predictions),
        "train_history": history,
        "output_file": str(OUTPUT_FILE),
        "model_file": str(MODEL_FILE),
        "note": "PyTorch implementation using a compact Mamba-style selective state-space scan.",
    }
    METRICS_FILE.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "feature_mean": feature_mean,
            "feature_std": feature_std,
            "target_mean": target_mean,
            "target_std": target_std,
            "feature_columns": FEATURE_COLUMNS,
            "target_columns": TARGET_COLUMNS,
            "config": {
                "window_size": WINDOW_SIZE,
                "prediction_horizon": PREDICTION_HORIZON,
                "model_dim": MODEL_DIM,
                "model_depth": MODEL_DEPTH,
                "dropout": DROPOUT,
            },
        },
        MODEL_FILE,
    )

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Generated metrics: {METRICS_FILE}")
    print(f"Saved model: {MODEL_FILE}")
    print(f"Windows: {len(metadata)} train={len(train_indices)} test={len(test_indices)}")


if __name__ == "__main__":
    main()
