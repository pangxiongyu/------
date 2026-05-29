from __future__ import annotations

from src.mpc.dynamics import PointMassState, WindVector
from src.mpc.robust_mpc import ConstrainedRobustMPC


def test_qp_mpc_tracks_short_route_with_constraints() -> None:
    controller = ConstrainedRobustMPC(dt=1.0, horizon=3, max_acc=2.0, max_speed=10.0)
    result = controller.track(
        initial_state=PointMassState(0.0, 0.0, 10.0),
        waypoints=[(0.0, 0.0, 10.0), (10.0, 0.0, 10.0)],
        winds=[WindVector(1.0, 0.0, 0.0)],
        steps_per_segment=3,
    )
    assert len(result.controls) == 3
    assert len(result.states) == 4
    assert result.mean_tracking_error >= 0.0
    assert all(abs(control.ax) <= 2.0001 for control in result.controls)

