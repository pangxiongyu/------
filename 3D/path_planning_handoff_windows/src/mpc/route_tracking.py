from __future__ import annotations

from dataclasses import dataclass

from src.core.geo_utils import waypoints_to_local_meters
from src.core.schemas import RoutePlan, Waypoint
from src.data_io.weather_loader import WeatherMap
from src.mpc.dynamics import PointMassState, WindVector
from src.mpc.robust_mpc import RobustMPCPrototype, TrackingResult
from src.mpc.wind_model import weather_cell_to_wind


@dataclass(frozen=True)
class RouteTrackingSummary:
    route: RoutePlan
    local_waypoints: list[Waypoint]
    winds: list[WindVector]
    tracking_result: TrackingResult


def winds_for_waypoints(
    weather_map: WeatherMap,
    waypoints: list[Waypoint],
    time: str | None = None,
) -> list[WindVector]:
    winds: list[WindVector] = []
    for latitude, longitude, height_m in waypoints:
        cell = weather_map.query_nearest(
            latitude=latitude,
            longitude=longitude,
            height_m=height_m,
            time=time,
        )
        winds.append(weather_cell_to_wind(cell))
    return winds


def track_route_with_weather(
    route: RoutePlan,
    weather_map: WeatherMap,
    time: str | None = None,
    controller: RobustMPCPrototype | None = None,
    steps_per_segment: int = 25,
    coordinate_scale: float = 1.0,
) -> RouteTrackingSummary:
    local_waypoints = waypoints_to_local_meters(route.waypoints)
    if coordinate_scale != 1.0:
        local_waypoints = [
            (x * coordinate_scale, y * coordinate_scale, z)
            for x, y, z in local_waypoints
        ]
    winds = winds_for_waypoints(weather_map, route.waypoints, time=time)
    if not local_waypoints:
        raise ValueError("Route has no waypoints.")
    active_controller = controller or RobustMPCPrototype()
    initial_state = PointMassState(*local_waypoints[0])
    tracking_result = active_controller.track(
        initial_state=initial_state,
        waypoints=local_waypoints,
        winds=winds,
        steps_per_segment=steps_per_segment,
    )
    return RouteTrackingSummary(
        route=route,
        local_waypoints=local_waypoints,
        winds=winds,
        tracking_result=tracking_result,
    )
