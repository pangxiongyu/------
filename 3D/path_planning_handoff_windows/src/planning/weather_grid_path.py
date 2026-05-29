from __future__ import annotations

import heapq
from dataclasses import dataclass

import pandas as pd

from src.core.geo_utils import haversine_distance_km, route_distance_km
from src.core.schemas import Waypoint
from src.data_io.weather_loader import WeatherMap


@dataclass(frozen=True)
class GridPathResult:
    waypoints: list[Waypoint]
    distance_km: float
    weather_cost_sum: float
    total_cost: float
    visited_count: int


class WeatherGridPathPlanner:
    """Weather-aware grid planner on one time slice and one height layer."""

    def __init__(
        self,
        weather_map: WeatherMap,
        time: str,
        height_m: float,
        weather_weight: float = 20.0,
        diagonal: bool = True,
    ) -> None:
        self.weather_map = weather_map
        self.time = time
        self.height_m = float(height_m)
        self.weather_weight = weather_weight
        self.diagonal = diagonal
        layer = weather_map.layer(time=time, height_m=height_m)
        if layer.empty:
            raise ValueError(f"No weather layer found for time={time}, height={height_m}")
        self.layer = layer.reset_index(drop=True)
        self._index_by_coord = {
            (float(row["latitude"]), float(row["longitude"])): index
            for index, row in self.layer.iterrows()
        }
        self._lats = sorted(float(value) for value in self.layer["latitude"].unique())
        self._lons = sorted(float(value) for value in self.layer["longitude"].unique())

    def _nearest_node(self, latitude: float, longitude: float) -> int:
        distances = (self.layer["latitude"] - latitude) ** 2 + (
            self.layer["longitude"] - longitude
        ) ** 2
        return int(distances.idxmin())

    def _row(self, node: int) -> pd.Series:
        return self.layer.iloc[node]

    def _neighbors(self, node: int) -> list[int]:
        row = self._row(node)
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        lat_index = self._lats.index(lat)
        lon_index = self._lons.index(lon)
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
            key = (self._lats[next_lat_index], self._lons[next_lon_index])
            next_node = self._index_by_coord.get(key)
            if next_node is not None:
                neighbors.append(next_node)
        return neighbors

    def _edge_cost(self, current: int, neighbor: int) -> float:
        current_row = self._row(current)
        neighbor_row = self._row(neighbor)
        distance = haversine_distance_km(
            float(current_row["latitude"]),
            float(current_row["longitude"]),
            float(neighbor_row["latitude"]),
            float(neighbor_row["longitude"]),
        )
        weather_cost = float(neighbor_row["cost"])
        return distance + self.weather_weight * weather_cost

    def _heuristic(self, current: int, goal: int) -> float:
        current_row = self._row(current)
        goal_row = self._row(goal)
        return haversine_distance_km(
            float(current_row["latitude"]),
            float(current_row["longitude"]),
            float(goal_row["latitude"]),
            float(goal_row["longitude"]),
        )

    def plan(
        self,
        start_lat: float,
        start_lon: float,
        goal_lat: float,
        goal_lon: float,
    ) -> GridPathResult:
        start = self._nearest_node(start_lat, start_lon)
        goal = self._nearest_node(goal_lat, goal_lon)

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
            raise RuntimeError("No grid path found between start and goal.")

        path_nodes = []
        current: int | None = goal
        while current is not None:
            path_nodes.append(current)
            current = came_from[current]
        path_nodes.reverse()

        waypoints = [
            (
                float(self._row(node)["latitude"]),
                float(self._row(node)["longitude"]),
                self.height_m,
            )
            for node in path_nodes
        ]
        distance_km = route_distance_km(waypoints)
        weather_cost_sum = sum(float(self._row(node)["cost"]) for node in path_nodes)
        return GridPathResult(
            waypoints=waypoints,
            distance_km=distance_km,
            weather_cost_sum=weather_cost_sum,
            total_cost=cost_so_far[goal],
            visited_count=visited_count,
        )

