from __future__ import annotations

from src.core.geo_utils import direct_waypoints, route_distance_km
from src.core.schemas import TaskState, UavState, Waypoint


def direct_route(uav: UavState, task: TaskState) -> list[Waypoint]:
    return direct_waypoints(
        uav.current_lat,
        uav.current_lon,
        uav.current_height_m,
        task.target_lat,
        task.target_lon,
        task.target_height_m,
    )


def direct_route_distance_km(uav: UavState, task: TaskState) -> float:
    return route_distance_km(direct_route(uav, task))

