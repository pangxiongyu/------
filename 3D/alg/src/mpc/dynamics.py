from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PointMassState:
    x: float
    y: float
    z: float
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0


@dataclass(frozen=True)
class ControlInput:
    ax: float
    ay: float
    az: float


@dataclass(frozen=True)
class WindVector:
    wx: float
    wy: float
    wz: float = 0.0


def clamp(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def wind_from_speed_direction(speed: float, direction_deg: float) -> WindVector:
    radians = math.radians(direction_deg)
    return WindVector(wx=speed * math.cos(radians), wy=speed * math.sin(radians), wz=0.0)


def step_point_mass(
    state: PointMassState,
    control: ControlInput,
    wind: WindVector,
    dt: float,
    max_speed: float = 20.0,
) -> PointMassState:
    vx = clamp(state.vx + control.ax * dt + wind.wx * dt * 0.05, max_speed)
    vy = clamp(state.vy + control.ay * dt + wind.wy * dt * 0.05, max_speed)
    vz = clamp(state.vz + control.az * dt + wind.wz * dt * 0.05, max_speed)
    return PointMassState(
        x=state.x + vx * dt,
        y=state.y + vy * dt,
        z=max(0.0, state.z + vz * dt),
        vx=vx,
        vy=vy,
        vz=vz,
    )

