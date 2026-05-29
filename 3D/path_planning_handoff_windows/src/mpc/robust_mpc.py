from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from src.core.schemas import Waypoint
from src.mpc.dynamics import (
    ControlInput,
    PointMassState,
    WindVector,
    clamp,
    step_point_mass,
)


@dataclass(frozen=True)
class TrackingResult:
    states: list[PointMassState]
    controls: list[ControlInput]
    tracking_errors: list[float]

    @property
    def mean_tracking_error(self) -> float:
        if not self.tracking_errors:
            return 0.0
        return sum(self.tracking_errors) / len(self.tracking_errors)


class RobustMPCPrototype:
    """A lightweight wind-compensating tracker.

    This is a practical placeholder for the first software milestone. It keeps
    the Robust MPC interface stable while a full constrained QP controller is
    added later with cvxpy/osqp.
    """

    def __init__(
        self,
        dt: float = 1.0,
        max_acc: float = 3.0,
        max_speed: float = 20.0,
        kp: float = 0.06,
        kd: float = 0.25,
    ) -> None:
        self.dt = dt
        self.max_acc = max_acc
        self.max_speed = max_speed
        self.kp = kp
        self.kd = kd

    def track(
        self,
        initial_state: PointMassState,
        waypoints: list[Waypoint],
        winds: list[WindVector] | None = None,
        steps_per_segment: int = 20,
    ) -> TrackingResult:
        if len(waypoints) < 2:
            return TrackingResult(states=[initial_state], controls=[], tracking_errors=[])

        state = initial_state
        states = [state]
        controls: list[ControlInput] = []
        errors: list[float] = []
        wind_sequence = winds or [WindVector(0.0, 0.0, 0.0)]

        for segment_index in range(len(waypoints) - 1):
            start = waypoints[segment_index]
            end = waypoints[segment_index + 1]
            for step_index in range(1, steps_per_segment + 1):
                ratio = step_index / steps_per_segment
                target_x = start[0] + (end[0] - start[0]) * ratio
                target_y = start[1] + (end[1] - start[1]) * ratio
                target_z = start[2] + (end[2] - start[2]) * ratio
                wind = wind_sequence[min(segment_index, len(wind_sequence) - 1)]

                error_x = target_x - state.x
                error_y = target_y - state.y
                error_z = target_z - state.z
                ax = clamp(self.kp * error_x - self.kd * state.vx - 0.05 * wind.wx, self.max_acc)
                ay = clamp(self.kp * error_y - self.kd * state.vy - 0.05 * wind.wy, self.max_acc)
                az = clamp(self.kp * error_z - self.kd * state.vz - 0.05 * wind.wz, self.max_acc)

                control = ControlInput(ax=ax, ay=ay, az=az)
                state = step_point_mass(
                    state,
                    control,
                    wind,
                    dt=self.dt,
                    max_speed=self.max_speed,
                )
                controls.append(control)
                states.append(state)
                errors.append(math.dist((state.x, state.y, state.z), (target_x, target_y, target_z)))

        return TrackingResult(states=states, controls=controls, tracking_errors=errors)


class ConstrainedRobustMPC:
    """Constrained receding-horizon MPC solved as a small QP.

    The model uses a 3D point-mass state `[x, y, z, vx, vy, vz]`, bounded
    acceleration, bounded velocity, and an additive wind disturbance in the
    velocity update. It is still a prototype, but it is now a real constrained
    optimization controller rather than a proportional tracker.
    """

    def __init__(
        self,
        dt: float = 1.0,
        horizon: int = 8,
        max_acc: float = 3.0,
        max_speed: float = 20.0,
        min_height_m: float = 0.0,
        max_height_m: float = 120.0,
        position_weight: float = 1.0,
        velocity_weight: float = 0.05,
        control_weight: float = 0.01,
        terminal_weight: float = 5.0,
        wind_gain: float = 0.05,
    ) -> None:
        self.dt = dt
        self.horizon = horizon
        self.max_acc = max_acc
        self.max_speed = max_speed
        self.min_height_m = min_height_m
        self.max_height_m = max_height_m
        self.position_weight = position_weight
        self.velocity_weight = velocity_weight
        self.control_weight = control_weight
        self.terminal_weight = terminal_weight
        self.wind_gain = wind_gain
        self._fallback = RobustMPCPrototype(
            dt=dt,
            max_acc=max_acc,
            max_speed=max_speed,
        )

    def track(
        self,
        initial_state: PointMassState,
        waypoints: list[Waypoint],
        winds: list[WindVector] | None = None,
        steps_per_segment: int = 20,
    ) -> TrackingResult:
        if len(waypoints) < 2:
            return TrackingResult(states=[initial_state], controls=[], tracking_errors=[])

        state = initial_state
        states = [state]
        controls: list[ControlInput] = []
        errors: list[float] = []
        wind_sequence = winds or [WindVector(0.0, 0.0, 0.0)]

        for segment_index in range(len(waypoints) - 1):
            start = waypoints[segment_index]
            end = waypoints[segment_index + 1]
            wind = wind_sequence[min(segment_index, len(wind_sequence) - 1)]
            for step_index in range(1, steps_per_segment + 1):
                references = self._reference_horizon(
                    start=start,
                    end=end,
                    step_index=step_index,
                    steps_per_segment=steps_per_segment,
                )
                control = self._solve_control(state, references, wind)
                state = step_point_mass(
                    state,
                    control,
                    wind,
                    dt=self.dt,
                    max_speed=self.max_speed,
                )
                target = references[0]
                controls.append(control)
                states.append(state)
                errors.append(math.dist((state.x, state.y, state.z), tuple(target)))

        return TrackingResult(states=states, controls=controls, tracking_errors=errors)

    def _reference_horizon(
        self,
        start: Waypoint,
        end: Waypoint,
        step_index: int,
        steps_per_segment: int,
    ) -> np.ndarray:
        references = []
        for horizon_step in range(self.horizon):
            ratio = min(1.0, (step_index + horizon_step) / steps_per_segment)
            references.append(
                [
                    start[0] + (end[0] - start[0]) * ratio,
                    start[1] + (end[1] - start[1]) * ratio,
                    start[2] + (end[2] - start[2]) * ratio,
                ]
            )
        return np.asarray(references, dtype=float)

    def _solve_control(
        self,
        state: PointMassState,
        references: np.ndarray,
        wind: WindVector,
    ) -> ControlInput:
        try:
            import cvxpy as cp
        except ImportError:
            return self._fallback_control(state, references[0], wind)

        horizon = self.horizon
        pos = cp.Variable((3, horizon + 1))
        vel = cp.Variable((3, horizon + 1))
        control = cp.Variable((3, horizon))
        wind_vec = np.asarray([wind.wx, wind.wy, wind.wz], dtype=float) * self.wind_gain

        constraints = [
            pos[:, 0] == np.asarray([state.x, state.y, state.z], dtype=float),
            vel[:, 0] == np.asarray([state.vx, state.vy, state.vz], dtype=float),
        ]
        objective = 0
        for step in range(horizon):
            constraints.extend(
                [
                    vel[:, step + 1] == vel[:, step] + control[:, step] * self.dt + wind_vec * self.dt,
                    pos[:, step + 1] == pos[:, step] + vel[:, step + 1] * self.dt,
                    control[:, step] <= self.max_acc,
                    control[:, step] >= -self.max_acc,
                    vel[:, step + 1] <= self.max_speed,
                    vel[:, step + 1] >= -self.max_speed,
                    pos[2, step + 1] >= self.min_height_m,
                    pos[2, step + 1] <= self.max_height_m,
                ]
            )
            ref = references[min(step, len(references) - 1)]
            objective += self.position_weight * cp.sum_squares(pos[:, step + 1] - ref)
            objective += self.velocity_weight * cp.sum_squares(vel[:, step + 1])
            objective += self.control_weight * cp.sum_squares(control[:, step])

        objective += self.terminal_weight * cp.sum_squares(pos[:, horizon] - references[-1])
        problem = cp.Problem(cp.Minimize(objective), constraints)
        try:
            problem.solve(solver=cp.OSQP, warm_start=True, verbose=False)
        except Exception:
            return self._fallback_control(state, references[0], wind)

        if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE} or control.value is None:
            return self._fallback_control(state, references[0], wind)

        first_control = control.value[:, 0]
        return ControlInput(
            ax=float(np.clip(first_control[0], -self.max_acc, self.max_acc)),
            ay=float(np.clip(first_control[1], -self.max_acc, self.max_acc)),
            az=float(np.clip(first_control[2], -self.max_acc, self.max_acc)),
        )

    def _fallback_control(
        self,
        state: PointMassState,
        target: np.ndarray,
        wind: WindVector,
    ) -> ControlInput:
        one_step = self._fallback.track(
            initial_state=state,
            waypoints=[(state.x, state.y, state.z), tuple(float(value) for value in target)],
            winds=[wind],
            steps_per_segment=1,
        )
        if one_step.controls:
            return one_step.controls[0]
        return ControlInput(0.0, 0.0, 0.0)
