from __future__ import annotations

from src.core.geo_utils import (
    latlon_to_local_xy_m,
    max_route_segment_distance_km,
    waypoints_to_local_meters,
)


def test_waypoints_to_local_meters_starts_at_origin() -> None:
    waypoints = [(30.0, 110.0, 10.0), (30.01, 110.01, 20.0)]
    local = waypoints_to_local_meters(waypoints)
    assert local[0] == (0.0, 0.0, 10.0)
    assert local[1][0] > 0.0
    assert local[1][1] > 0.0
    assert local[1][2] == 20.0


def test_latlon_to_local_xy_m_has_zero_for_origin() -> None:
    assert latlon_to_local_xy_m(30.0, 110.0, 30.0, 110.0) == (0.0, 0.0)


def test_max_route_segment_distance_uses_longest_leg() -> None:
    route = [
        (0.0, 0.0, 10.0),
        (0.0, 1.0, 10.0),
        (0.0, 3.0, 10.0),
    ]

    assert 222.0 < max_route_segment_distance_km(route) < 224.0
