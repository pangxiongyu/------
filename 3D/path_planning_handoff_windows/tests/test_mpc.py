from __future__ import annotations

from src.mpc.dynamics import PointMassState
from src.mpc.robust_mpc import RobustMPCPrototype


def test_mpc_prototype_tracks_nonempty_route() -> None:
    controller = RobustMPCPrototype(dt=1.0)
    result = controller.track(
        initial_state=PointMassState(0.0, 0.0, 10.0),
        waypoints=[(0.0, 0.0, 10.0), (20.0, 0.0, 10.0)],
        steps_per_segment=5,
    )
    assert len(result.states) == 6
    assert len(result.controls) == 5
    assert result.mean_tracking_error >= 0.0

