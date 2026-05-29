from __future__ import annotations

from demo_setup import build_demo_problem

from src.marl.env import MultiUavTaskEnv
from src.marl.policy import greedy_policy_actions


def main() -> None:
    weather_map, uavs, tasks, time = build_demo_problem()
    height_layers = weather_map.height_layers
    route_strategies = ["direct", "weather_grid"]
    env = MultiUavTaskEnv(
        uavs,
        tasks,
        weather_map,
        time=time,
        max_steps=3,
        height_layers=height_layers,
        use_weather_grid_paths=True,
        route_strategies=route_strategies,
    )
    observations = env.reset()
    print("Initial observation keys:", list(observations))

    done = False
    total_rewards = {uav.uav_id: 0.0 for uav in uavs}
    while not done:
        live_tasks = list(env.tasks.values())
        live_uavs = list(env.uavs.values())
        actions = greedy_policy_actions(
            live_uavs,
            live_tasks,
            weather_map,
            time=time,
            height_layers=height_layers,
            route_strategies=route_strategies,
        )
        _, rewards, done, info = env.step(actions)
        for uav_id, reward in rewards.items():
            total_rewards[uav_id] += reward
        print("actions:", actions)
        print("rewards:", {key: round(value, 3) for key, value in rewards.items()})
        print("events:", info["events"])

    print("total_rewards:", {key: round(value, 3) for key, value in total_rewards.items()})


if __name__ == "__main__":
    main()
