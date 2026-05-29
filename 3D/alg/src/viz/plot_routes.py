from __future__ import annotations

from pathlib import Path

from src.core.schemas import RoutePlan


def plot_routes(routes: list[RoutePlan], output_path: str | Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 6))
    for route in routes:
        lats = [point[0] for point in route.waypoints]
        lons = [point[1] for point in route.waypoints]
        ax.plot(lons, lats, marker="o", label=f"{route.uav_id}->{route.task_id}")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title("Assigned direct routes")
    if routes:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)

