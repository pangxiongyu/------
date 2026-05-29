from __future__ import annotations

import math

from src.core.schemas import Waypoint


EARTH_RADIUS_KM = 6371.0088
EARTH_RADIUS_M = EARTH_RADIUS_KM * 1000.0


def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Great-circle distance between two latitude/longitude points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def waypoint_distance_km(start: Waypoint, end: Waypoint) -> float:
    horizontal = haversine_distance_km(start[0], start[1], end[0], end[1])
    vertical = abs(end[2] - start[2]) / 1000.0
    return math.sqrt(horizontal**2 + vertical**2)


def route_distance_km(waypoints: list[Waypoint]) -> float:
    if len(waypoints) < 2:
        return 0.0
    return sum(
        waypoint_distance_km(waypoints[index], waypoints[index + 1])
        for index in range(len(waypoints) - 1)
    )


def max_route_segment_distance_km(waypoints: list[Waypoint]) -> float:
    if len(waypoints) < 2:
        return 0.0
    return max(
        waypoint_distance_km(waypoints[index], waypoints[index + 1])
        for index in range(len(waypoints) - 1)
    )


def direct_waypoints(
    start_lat: float,
    start_lon: float,
    start_height_m: float,
    target_lat: float,
    target_lon: float,
    target_height_m: float,
) -> list[Waypoint]:
    return [
        (start_lat, start_lon, start_height_m),
        (target_lat, target_lon, target_height_m),
    ]


def latlon_to_local_xy_m(
    origin_lat: float,
    origin_lon: float,
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """Approximate local tangent-plane coordinates in meters.

    x is east, y is north. This is accurate enough for the first MPC prototype
    and keeps the controller independent from latitude/longitude units.
    """
    d_lat = math.radians(latitude - origin_lat)
    d_lon = math.radians(longitude - origin_lon)
    origin_phi = math.radians(origin_lat)
    x = EARTH_RADIUS_M * d_lon * math.cos(origin_phi)
    y = EARTH_RADIUS_M * d_lat
    return x, y


def waypoints_to_local_meters(waypoints: list[Waypoint]) -> list[Waypoint]:
    if not waypoints:
        return []
    origin_lat, origin_lon, _ = waypoints[0]
    local: list[Waypoint] = []
    for latitude, longitude, height_m in waypoints:
        x, y = latlon_to_local_xy_m(origin_lat, origin_lon, latitude, longitude)
        local.append((x, y, height_m))
    return local
