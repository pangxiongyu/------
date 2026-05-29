from __future__ import annotations

import heapq

import pandas as pd

from src.core.geo_utils import route_distance_km, waypoint_distance_km
from src.core.schemas import Waypoint
from src.data_io.weather_loader import WeatherMap
from src.planning.weather_grid_path import GridPathResult


class Weather3DPathPlanner:
    """Weather-aware path planner across latitude, longitude, and height layers."""

    def __init__(
        self,
        weather_map: WeatherMap,
        time: str,
        weather_weight: float = 20.0,
        altitude_weight: float = 0.5,
        diagonal: bool = True,
    ) -> None:
        self.weather_map = weather_map
        self.time = time
        self.weather_weight = weather_weight
        self.altitude_weight = altitude_weight
        self.diagonal = diagonal
        layer = weather_map.layer(time=time)
        if layer.empty:
            raise ValueError(f"No weather cells found for time={time}")
        self.layer = layer.reset_index(drop=True)
        self._index_by_coord = {
            (float(row["latitude"]), float(row["longitude"]), float(row["height_m"])): index
            for index, row in self.layer.iterrows()
        }
        self._lats = sorted(float(value) for value in self.layer["latitude"].unique())
        self._lons = sorted(float(value) for value in self.layer["longitude"].unique())
        self._heights = sorted(float(value) for value in self.layer["height_m"].unique())

    def _row(self, node: int) -> pd.Series:
        return self.layer.iloc[node]

    def _waypoint(self, node: int) -> Waypoint:
        row = self._row(node)
        return (
            float(row["latitude"]),
            float(row["longitude"]),
            float(row["height_m"]),
        )

    def _nearest_node(self, latitude: float, longitude: float, height_m: float) -> int:
        height_scale = 111_000.0
        distances = (
            (self.layer["latitude"] - latitude) ** 2
            + (self.layer["longitude"] - longitude) ** 2
            + ((self.layer["height_m"] - height_m) / height_scale) ** 2
        )
        return int(distances.idxmin())

    def _neighbors(self, node: int) -> list[int]:
        lat, lon, height = self._waypoint(node)
        lat_index = self._lats.index(lat)
        lon_index = self._lons.index(lon)
        height_index = self._heights.index(height)

        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if self.diagonal:
            offsets.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

        neighbors: list[int] = []
        for d_lat, d_lon in offsets:
            next_lat_index = lat_index + d_lat
            next_lon_index = lon_index + d_lon
            if not (0 <= next_lat_index < len(self._lats)):
                continue
            if not (0 <= next_lon_index < len(self._lons)):
                continue
            key = (self._lats[next_lat_index], self._lons[next_lon_index], height)
            next_node = self._index_by_coord.get(key)
            if next_node is not None:
                neighbors.append(next_node)

        for d_height in (-1, 1):
            next_height_index = height_index + d_height
            if not (0 <= next_height_index < len(self._heights)):
                continue
            key = (lat, lon, self._heights[next_height_index])
            next_node = self._index_by_coord.get(key)
            if next_node is not None:
                neighbors.append(next_node)

        return neighbors

    def _edge_cost(self, current: int, neighbor: int) -> float:
        current_wp = self._waypoint(current)
        neighbor_wp = self._waypoint(neighbor)
        neighbor_row = self._row(neighbor)
        distance = waypoint_distance_km(current_wp, neighbor_wp)
        weather_cost = float(neighbor_row["cost"])
        altitude_change_m = abs(neighbor_wp[2] - current_wp[2])
        altitude_cost = self.altitude_weight * (altitude_change_m / 100.0)
        return distance + self.weather_weight * weather_cost + altitude_cost

    def _heuristic(self, current: int, goal: int) -> float:
        return waypoint_distance_km(self._waypoint(current), self._waypoint(goal))

    def plan(
        self,
        start_lat: float,
        start_lon: float,
        start_height_m: float,
        goal_lat: float,
        goal_lon: float,
        goal_height_m: float,
    ) -> GridPathResult:
        start = self._nearest_node(start_lat, start_lon, start_height_m)
        goal = self._nearest_node(goal_lat, goal_lon, goal_height_m)
        frontier: list[tuple[float, int]] = [(0.0, start)]
        came_from: dict[int, int | None] = {start: None}
        cost_so_far: dict[int, float] = {start: 0.0}
        visited_count = 0

        while frontier:
            _, current = heapq.heappop(frontier)
            visited_count += 1
            if current == goal:
                break
            for neighbor in self._neighbors(current):
                new_cost = cost_so_far[current] + self._edge_cost(current, neighbor)
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self._heuristic(neighbor, goal)
                    heapq.heappush(frontier, (priority, neighbor))
                    came_from[neighbor] = current

        if goal not in came_from:
            raise RuntimeError("No 3D weather path found between start and goal.")

        path_nodes = []
        current: int | None = goal
        while current is not None:
            path_nodes.append(current)
            current = came_from[current]
        path_nodes.reverse()

        waypoints = [self._waypoint(node) for node in path_nodes]
        weather_cost_sum = sum(float(self._row(node)["cost"]) for node in path_nodes)
        return GridPathResult(
            waypoints=waypoints,
            distance_km=route_distance_km(waypoints),
            weather_cost_sum=weather_cost_sum,
            total_cost=cost_so_far[goal],
            visited_count=visited_count,
        )

