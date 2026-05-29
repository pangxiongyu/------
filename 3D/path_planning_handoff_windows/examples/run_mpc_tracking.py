from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.mpc.dynamics import PointMassState, WindVector
from src.mpc.robust_mpc import RobustMPCPrototype


def main() -> None:
    waypoints = [(0.0, 0.0, 10.0), (100.0, 40.0, 30.0), (180.0, 80.0, 20.0)]
    winds = [WindVector(3.0, 1.0, 0.0), WindVector(5.0, -2.0, 0.0)]
    controller = RobustMPCPrototype(dt=1.0)
    result = controller.track(
        initial_state=PointMassState(*waypoints[0]),
        waypoints=waypoints,
        winds=winds,
        steps_per_segment=25,
    )
    print("states:", len(result.states))
    print("controls:", len(result.controls))
    print("mean_tracking_error:", round(result.mean_tracking_error, 4))
    print("final_state:", result.states[-1])


if __name__ == "__main__":
    main()
