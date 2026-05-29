from __future__ import annotations


WAIT_ACTION = "wait"
HEIGHT_SEPARATOR = "@"
STRATEGY_SEPARATOR = "#"
DEFAULT_ROUTE_STRATEGY = "direct"
WEATHER_GRID_ROUTE_STRATEGY = "weather_grid"
WEATHER_3D_ROUTE_STRATEGY = "weather_3d"


def encode_task_action(
    task_id: str,
    height_m: float | None = None,
    route_strategy: str | None = None,
) -> str:
    action = task_id
    if height_m is not None:
        height_text = f"{float(height_m):g}"
        action = f"{action}{HEIGHT_SEPARATOR}{height_text}m"
    if route_strategy:
        action = f"{action}{STRATEGY_SEPARATOR}{route_strategy}"
    return action


def parse_planning_action(action: str | int | None) -> tuple[str | None, float | None, str | None]:
    if action is None:
        return None, None, None
    action_text = str(action)
    if action_text.lower() == WAIT_ACTION:
        return None, None, None

    route_strategy: str | None = None
    if STRATEGY_SEPARATOR in action_text:
        action_text, route_strategy = action_text.split(STRATEGY_SEPARATOR, maxsplit=1)
        route_strategy = route_strategy.strip() or None

    if HEIGHT_SEPARATOR not in action_text:
        return action_text, None, route_strategy

    task_id, height_text = action_text.split(HEIGHT_SEPARATOR, maxsplit=1)
    return task_id, _parse_height_text(height_text), route_strategy


def parse_task_action(action: str | int | None) -> tuple[str | None, float | None]:
    task_id, height_m, _ = parse_planning_action(action)
    return task_id, height_m


def parse_task_action_with_strategy(action: str | int | None) -> tuple[str | None, float | None, str | None]:
    return parse_planning_action(action)


def _parse_height_text(height_text: str) -> float:
    height_text = height_text.strip()
    if height_text.endswith("m"):
        height_text = height_text[:-1]
    return float(height_text)


def build_task_actions(
    task_ids: list[str],
    height_layers: list[float] | None = None,
    route_strategies: list[str] | None = None,
) -> list[str]:
    if not height_layers:
        if not route_strategies:
            return [WAIT_ACTION, *task_ids]
        return [
            WAIT_ACTION,
            *[
                encode_task_action(task_id, route_strategy=strategy)
                for task_id in task_ids
                for strategy in route_strategies
            ],
        ]
    actions = [WAIT_ACTION]
    for task_id in task_ids:
        for height_m in height_layers:
            if route_strategies:
                for strategy in route_strategies:
                    actions.append(encode_task_action(task_id, height_m, strategy))
            else:
                actions.append(encode_task_action(task_id, height_m))
    return actions
