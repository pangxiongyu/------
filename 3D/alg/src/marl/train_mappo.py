from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import torch
from torch import nn
from torch.distributions import Categorical

from src.marl.action_space import (
    DEFAULT_ROUTE_STRATEGY,
    WAIT_ACTION,
    WEATHER_3D_ROUTE_STRATEGY,
    WEATHER_GRID_ROUTE_STRATEGY,
    parse_task_action_with_strategy,
)
from src.marl.env import MultiUavTaskEnv


@dataclass
class Transition:
    obs: list[float]
    global_obs: list[float]
    action: int
    old_log_prob: float
    reward: float
    raw_reward: float
    done: bool
    mask: list[bool]


@dataclass
class TrainingStats:
    episode_rewards: list[float]
    scaled_episode_rewards: list[float]
    policy_losses: list[float]
    value_losses: list[float]
    return_means: list[float]
    return_stds: list[float]

    def rows(self) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for index, reward in enumerate(self.episode_rewards, start=1):
            rows.append(
                {
                    "episode": float(index),
                    "episode_reward": reward,
                    "scaled_episode_reward": self.scaled_episode_rewards[index - 1],
                    "policy_loss": self.policy_losses[index - 1],
                    "value_loss": self.value_losses[index - 1],
                    "return_mean": self.return_means[index - 1],
                    "return_std": self.return_stds[index - 1],
                }
            )
        return rows


@dataclass
class CheckpointEvalRecord:
    episode: int
    metrics: dict[str, float]
    is_best: bool = False

    def row(self) -> dict[str, float]:
        return {
            "episode": float(self.episode),
            "is_best": float(self.is_best),
            **self.metrics,
        }


def checkpoint_selection_key(
    metrics: dict[str, float],
    selection_mode: str = "reward",
) -> tuple[float, ...]:
    completed = float(metrics.get("mean_completed_task_count", 0.0))
    reward = float(metrics.get("mean_total_reward", 0.0))
    path_cost = float(metrics.get("mean_total_path_cost", 0.0))
    peak_segment = float(metrics.get("mean_peak_segment_distance_km", 0.0))
    if selection_mode == "path_cost":
        return (completed, -path_cost, reward)
    if selection_mode in {"trackability", "mpc_proxy"}:
        return (completed, -peak_segment, -path_cost, reward)
    return (
        completed,
        reward,
        -path_cost,
    )


def aggregate_policy_metrics(metrics_by_scenario: list[dict[str, float]]) -> dict[str, float]:
    if not metrics_by_scenario:
        return {"validation_scenario_count": 0.0}
    keys = sorted({key for metrics in metrics_by_scenario for key in metrics})
    aggregated = {
        key: sum(metrics.get(key, 0.0) for metrics in metrics_by_scenario) / len(metrics_by_scenario)
        for key in keys
    }
    aggregated["validation_scenario_count"] = float(len(metrics_by_scenario))
    return aggregated


class ActorCritic(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        global_obs_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
    ) -> None:
        super().__init__()
        self.actor = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )
        self.critic = nn.Sequential(
            nn.Linear(global_obs_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def masked_logits(self, obs: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        logits = self.actor(obs)
        return logits.masked_fill(~mask, -1.0e9)

    def value(self, global_obs: torch.Tensor) -> torch.Tensor:
        return self.critic(global_obs).squeeze(-1)


class MAPPOPrototypeTrainer:
    """Runnable MAPPO-style trainer for the project prototype.

    This is deliberately compact: it is enough to validate the environment,
    reward design, and train/eval wiring. Later work can replace this class with
    a full MAPPO implementation while keeping the environment API unchanged.
    """

    def __init__(
        self,
        env_factory: Callable[[], MultiUavTaskEnv],
        episodes: int = 20,
        gamma: float = 0.95,
        clip_ratio: float = 0.2,
        ppo_epochs: int = 4,
        lr: float = 3e-4,
        reward_scale: float = 0.01,
        normalize_value_targets: bool = True,
        mask_wait_when_tasks_available: bool = True,
        seed: int | None = None,
        device: str | None = None,
    ) -> None:
        if seed is not None:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        self.env_factory = env_factory
        self.episodes = episodes
        self.gamma = gamma
        self.clip_ratio = clip_ratio
        self.ppo_epochs = ppo_epochs
        self.lr = lr
        self.reward_scale = reward_scale
        self.normalize_value_targets = normalize_value_targets
        self.mask_wait_when_tasks_available = mask_wait_when_tasks_available
        self.seed = seed
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        probe_env = env_factory()
        probe_obs = probe_env.reset()
        self.agent_ids = sorted(probe_obs)
        first_agent = self.agent_ids[0]
        self.action_names = list(probe_env.valid_actions()[first_agent])
        self.obs_dim = len(next(iter(probe_obs.values())))
        self.global_obs_dim = self.obs_dim * len(self.agent_ids)
        self.action_dim = len(self.action_names)
        self.model = ActorCritic(
            obs_dim=self.obs_dim,
            global_obs_dim=self.global_obs_dim,
            action_dim=self.action_dim,
        ).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    def _global_obs(self, observations: dict[str, list[float]]) -> list[float]:
        values: list[float] = []
        for agent_id in self.agent_ids:
            values.extend(observations[agent_id])
        return values

    def _mask_for_agent(self, valid_actions: list[str]) -> list[bool]:
        valid = set(valid_actions)
        mask = [action_name in valid for action_name in self.action_names]
        if self.mask_wait_when_tasks_available:
            has_task_action = any(action_name != WAIT_ACTION for action_name in valid_actions)
            if has_task_action and WAIT_ACTION in self.action_names:
                mask[self.action_names.index(WAIT_ACTION)] = False
        return mask

    def _sample_action(
        self,
        obs: list[float],
        mask: list[bool],
    ) -> tuple[int, float]:
        obs_tensor = torch.tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
        mask_tensor = torch.tensor(mask, dtype=torch.bool, device=self.device).unsqueeze(0)
        logits = self.model.masked_logits(obs_tensor, mask_tensor)
        distribution = Categorical(logits=logits)
        action = distribution.sample()
        log_prob = distribution.log_prob(action)
        return int(action.item()), float(log_prob.item())

    def _greedy_action(self, obs: list[float], mask: list[bool]) -> int:
        obs_tensor = torch.tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
        mask_tensor = torch.tensor(mask, dtype=torch.bool, device=self.device).unsqueeze(0)
        with torch.no_grad():
            logits = self.model.masked_logits(obs_tensor, mask_tensor)
            action = torch.argmax(logits, dim=-1)
        return int(action.item())

    def collect_episode(self) -> tuple[list[Transition], float, float]:
        env = self.env_factory()
        observations = env.reset()
        transitions: list[Transition] = []
        episode_reward = 0.0
        scaled_episode_reward = 0.0
        done = False

        while not done:
            global_obs = self._global_obs(observations)
            valid_actions = env.valid_actions()
            env_actions: dict[str, str] = {}
            pending: list[tuple[str, list[float], list[bool], int, float]] = []

            for agent_id in self.agent_ids:
                obs = observations[agent_id]
                mask = self._mask_for_agent(valid_actions[agent_id])
                action_index, log_prob = self._sample_action(obs, mask)
                action_name = self.action_names[action_index]
                env_actions[agent_id] = action_name
                pending.append((agent_id, obs, mask, action_index, log_prob))

            next_observations, rewards, done, _ = env.step(env_actions)
            for agent_id, obs, mask, action_index, log_prob in pending:
                raw_reward = rewards[agent_id]
                reward = raw_reward * self.reward_scale
                episode_reward += raw_reward
                scaled_episode_reward += reward
                transitions.append(
                    Transition(
                        obs=obs,
                        global_obs=global_obs,
                        action=action_index,
                        old_log_prob=log_prob,
                        reward=reward,
                        raw_reward=raw_reward,
                        done=done,
                        mask=mask,
                    )
                )
            observations = next_observations

        return transitions, episode_reward, scaled_episode_reward

    def _discounted_returns(self, transitions: list[Transition]) -> list[float]:
        returns = [0.0 for _ in transitions]
        running = {agent_id: 0.0 for agent_id in self.agent_ids}
        # Transitions are stored in agent order at each step.
        for index in range(len(transitions) - 1, -1, -1):
            agent_id = self.agent_ids[index % len(self.agent_ids)]
            transition = transitions[index]
            if transition.done:
                running[agent_id] = 0.0
            running[agent_id] = transition.reward + self.gamma * running[agent_id]
            returns[index] = running[agent_id]
        return returns

    def _value_targets(self, returns: torch.Tensor) -> tuple[torch.Tensor, float, float]:
        mean = float(returns.mean().detach().cpu().item()) if returns.numel() else 0.0
        if returns.numel() > 1:
            std_tensor = returns.std()
            std = float(std_tensor.detach().cpu().item())
        else:
            std = 1.0
        if not self.normalize_value_targets or returns.numel() <= 1:
            return returns, mean, max(std, 1e-6)
        return (returns - returns.mean()) / (returns.std() + 1e-6), mean, max(std, 1e-6)

    def update(self, transitions: list[Transition]) -> tuple[float, float, float, float]:
        if not transitions:
            return 0.0, 0.0, 0.0, 0.0

        obs = torch.tensor([item.obs for item in transitions], dtype=torch.float32, device=self.device)
        global_obs = torch.tensor(
            [item.global_obs for item in transitions],
            dtype=torch.float32,
            device=self.device,
        )
        actions = torch.tensor([item.action for item in transitions], dtype=torch.long, device=self.device)
        old_log_probs = torch.tensor(
            [item.old_log_prob for item in transitions],
            dtype=torch.float32,
            device=self.device,
        )
        masks = torch.tensor([item.mask for item in transitions], dtype=torch.bool, device=self.device)
        raw_returns = torch.tensor(self._discounted_returns(transitions), dtype=torch.float32, device=self.device)
        value_targets, return_mean, return_std = self._value_targets(raw_returns)

        policy_loss_value = 0.0
        value_loss_value = 0.0
        for _ in range(self.ppo_epochs):
            logits = self.model.masked_logits(obs, masks)
            distribution = Categorical(logits=logits)
            log_probs = distribution.log_prob(actions)
            entropy = distribution.entropy().mean()
            values = self.model.value(global_obs)
            advantages = value_targets - values.detach()
            if advantages.numel() > 1:
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-6)

            ratios = torch.exp(log_probs - old_log_probs)
            clipped = torch.clamp(ratios, 1.0 - self.clip_ratio, 1.0 + self.clip_ratio)
            policy_loss = -torch.min(ratios * advantages, clipped * advantages).mean()
            value_loss = nn.functional.mse_loss(values, value_targets)
            loss = policy_loss + 0.5 * value_loss - 0.01 * entropy

            self.optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            policy_loss_value = float(policy_loss.detach().cpu().item())
            value_loss_value = float(value_loss.detach().cpu().item())

        return policy_loss_value, value_loss_value, return_mean, return_std

    def train(self) -> TrainingStats:
        episode_rewards: list[float] = []
        scaled_episode_rewards: list[float] = []
        policy_losses: list[float] = []
        value_losses: list[float] = []
        return_means: list[float] = []
        return_stds: list[float] = []
        for _ in range(self.episodes):
            transitions, episode_reward, scaled_episode_reward = self.collect_episode()
            policy_loss, value_loss, return_mean, return_std = self.update(transitions)
            episode_rewards.append(episode_reward)
            scaled_episode_rewards.append(scaled_episode_reward)
            policy_losses.append(policy_loss)
            value_losses.append(value_loss)
            return_means.append(return_mean)
            return_stds.append(return_std)
        return TrainingStats(
            episode_rewards=episode_rewards,
            scaled_episode_rewards=scaled_episode_rewards,
            policy_losses=policy_losses,
            value_losses=value_losses,
            return_means=return_means,
            return_stds=return_stds,
        )

    def train_with_eval_checkpoints(
        self,
        best_checkpoint_path: str | Path,
        eval_interval: int = 1,
        eval_episodes: int = 1,
        eval_env_factories: list[Callable[[], MultiUavTaskEnv]] | None = None,
        checkpoint_selection_mode: str = "reward",
    ) -> tuple[TrainingStats, list[CheckpointEvalRecord]]:
        episode_rewards: list[float] = []
        scaled_episode_rewards: list[float] = []
        policy_losses: list[float] = []
        value_losses: list[float] = []
        return_means: list[float] = []
        return_stds: list[float] = []
        records: list[CheckpointEvalRecord] = []
        best_key: tuple[float, float, float] | None = None
        interval = max(1, int(eval_interval))

        for episode in range(1, self.episodes + 1):
            transitions, episode_reward, scaled_episode_reward = self.collect_episode()
            policy_loss, value_loss, return_mean, return_std = self.update(transitions)
            episode_rewards.append(episode_reward)
            scaled_episode_rewards.append(scaled_episode_reward)
            policy_losses.append(policy_loss)
            value_losses.append(value_loss)
            return_means.append(return_mean)
            return_stds.append(return_std)

            should_eval = episode == self.episodes or episode % interval == 0
            if should_eval:
                if eval_env_factories:
                    metrics = self.evaluate_policy_across_envs(
                        eval_env_factories,
                        episodes=eval_episodes,
                        deterministic=True,
                    )
                else:
                    metrics = self.evaluate_policy(episodes=eval_episodes, deterministic=True)
                selection_key = checkpoint_selection_key(metrics, checkpoint_selection_mode)
                is_best = best_key is None or selection_key > best_key
                if is_best:
                    best_key = selection_key
                    self.save_checkpoint(best_checkpoint_path)
                records.append(
                    CheckpointEvalRecord(
                        episode=episode,
                        metrics=metrics,
                        is_best=is_best,
                    )
                )

        return (
            TrainingStats(
                episode_rewards=episode_rewards,
                scaled_episode_rewards=scaled_episode_rewards,
                policy_losses=policy_losses,
                value_losses=value_losses,
                return_means=return_means,
                return_stds=return_stds,
            ),
            records,
        )

    def policy_actions(
        self,
        observations: dict[str, list[float]],
        valid_actions: dict[str, list[str]],
        deterministic: bool = True,
        avoid_duplicate_tasks: bool = False,
    ) -> dict[str, str]:
        actions: dict[str, str] = {}
        claimed_tasks: set[str] = set()
        for agent_id in self.agent_ids:
            obs = observations[agent_id]
            mask = self._mask_for_agent(valid_actions[agent_id])
            if avoid_duplicate_tasks and claimed_tasks:
                for index, action_name in enumerate(self.action_names):
                    task_id, _, _ = parse_task_action_with_strategy(action_name)
                    if task_id in claimed_tasks:
                        mask[index] = False
                if not any(mask):
                    actions[agent_id] = WAIT_ACTION
                    continue
            if deterministic:
                action_index = self._greedy_action(obs, mask)
            else:
                action_index, _ = self._sample_action(obs, mask)
            action_name = self.action_names[action_index]
            actions[agent_id] = action_name
            task_id, _, _ = parse_task_action_with_strategy(action_name)
            if avoid_duplicate_tasks and task_id is not None:
                claimed_tasks.add(task_id)
        return actions

    def evaluate_policy(
        self,
        episodes: int = 1,
        deterministic: bool = True,
        avoid_duplicate_tasks: bool = True,
        env_factory: Callable[[], MultiUavTaskEnv] | None = None,
    ) -> dict[str, float]:
        total_rewards: list[float] = []
        completed_counts: list[float] = []
        average_weather_costs: list[float] = []
        total_path_costs: list[float] = []
        total_distances: list[float] = []
        conflict_counts: list[float] = []
        direct_action_counts: list[float] = []
        weather_grid_action_counts: list[float] = []
        weather_3d_action_counts: list[float] = []
        average_max_segment_distances: list[float] = []
        peak_segment_distances: list[float] = []
        trackability_penalties: list[float] = []
        active_env_factory = env_factory or self.env_factory

        for _ in range(episodes):
            env = active_env_factory()
            observations = env.reset()
            missing_agents = [agent_id for agent_id in self.agent_ids if agent_id not in observations]
            if missing_agents:
                raise ValueError(
                    "Evaluation environment is missing trained agents: "
                    f"{missing_agents}"
                )
            done = False
            total_reward = 0.0
            completed = 0
            weather_sum = 0.0
            path_cost_sum = 0.0
            distance_sum = 0.0
            conflicts = 0
            max_segment_sum = 0.0
            peak_segment = 0.0
            trackability_penalty_sum = 0.0
            strategy_counts = {
                DEFAULT_ROUTE_STRATEGY: 0,
                WEATHER_GRID_ROUTE_STRATEGY: 0,
                WEATHER_3D_ROUTE_STRATEGY: 0,
            }

            while not done:
                actions = self.policy_actions(
                    observations,
                    env.valid_actions(),
                    deterministic=deterministic,
                    avoid_duplicate_tasks=avoid_duplicate_tasks,
                )
                observations, rewards, done, info = env.step(actions)
                total_reward += sum(rewards.values())
                for event in info["events"]:
                    if event.get("event") == "completed":
                        completed += 1
                        route_strategy = str(event.get("route_strategy", DEFAULT_ROUTE_STRATEGY))
                        if route_strategy in strategy_counts:
                            strategy_counts[route_strategy] += 1
                        weather_sum += float(event.get("weather_cost", 0.0))
                        path_cost_sum += float(event.get("path_cost", 0.0))
                        distance_sum += float(event.get("distance_km", 0.0))
                        max_segment_distance = float(event.get("max_segment_distance_km", 0.0))
                        max_segment_sum += max_segment_distance
                        peak_segment = max(peak_segment, max_segment_distance)
                        trackability_penalty_sum += float(event.get("trackability_penalty", 0.0))
                    elif event.get("event") in {
                        "conflict",
                        "invalid_task",
                        "payload_overload",
                        "invalid_route_strategy",
                    }:
                        conflicts += 1

            total_rewards.append(total_reward)
            completed_counts.append(float(completed))
            average_weather_costs.append(weather_sum / completed if completed else 0.0)
            total_path_costs.append(path_cost_sum)
            total_distances.append(distance_sum)
            conflict_counts.append(float(conflicts))
            direct_action_counts.append(float(strategy_counts[DEFAULT_ROUTE_STRATEGY]))
            weather_grid_action_counts.append(float(strategy_counts[WEATHER_GRID_ROUTE_STRATEGY]))
            weather_3d_action_counts.append(float(strategy_counts[WEATHER_3D_ROUTE_STRATEGY]))
            average_max_segment_distances.append(max_segment_sum / completed if completed else 0.0)
            peak_segment_distances.append(peak_segment)
            trackability_penalties.append(trackability_penalty_sum)

        return {
            "episodes": float(episodes),
            "mean_total_reward": sum(total_rewards) / episodes,
            "mean_completed_task_count": sum(completed_counts) / episodes,
            "mean_average_weather_cost": sum(average_weather_costs) / episodes,
            "mean_total_path_cost": sum(total_path_costs) / episodes,
            "mean_total_distance_km": sum(total_distances) / episodes,
            "mean_conflict_count": sum(conflict_counts) / episodes,
            "mean_direct_action_count": sum(direct_action_counts) / episodes,
            "mean_weather_grid_action_count": sum(weather_grid_action_counts) / episodes,
            "mean_weather_3d_action_count": sum(weather_3d_action_counts) / episodes,
            "mean_average_max_segment_distance_km": sum(average_max_segment_distances) / episodes,
            "mean_peak_segment_distance_km": sum(peak_segment_distances) / episodes,
            "mean_trackability_penalty": sum(trackability_penalties) / episodes,
        }

    def evaluate_policy_across_envs(
        self,
        env_factories: list[Callable[[], MultiUavTaskEnv]],
        episodes: int = 1,
        deterministic: bool = True,
        avoid_duplicate_tasks: bool = True,
    ) -> dict[str, float]:
        metrics_by_scenario = [
            self.evaluate_policy(
                episodes=episodes,
                deterministic=deterministic,
                avoid_duplicate_tasks=avoid_duplicate_tasks,
                env_factory=env_factory,
            )
            for env_factory in env_factories
        ]
        return aggregate_policy_metrics(metrics_by_scenario)

    def save_checkpoint(self, path: str | Path) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "agent_ids": self.agent_ids,
                "action_names": self.action_names,
                "obs_dim": self.obs_dim,
                "global_obs_dim": self.global_obs_dim,
                "action_dim": self.action_dim,
                "hyperparameters": {
                    "episodes": self.episodes,
                    "gamma": self.gamma,
                    "clip_ratio": self.clip_ratio,
                    "ppo_epochs": self.ppo_epochs,
                    "lr": self.lr,
                    "reward_scale": self.reward_scale,
                    "normalize_value_targets": self.normalize_value_targets,
                    "mask_wait_when_tasks_available": self.mask_wait_when_tasks_available,
                    "seed": -1 if self.seed is None else self.seed,
                },
            },
            output_path,
        )

    def load_checkpoint(self, path: str | Path) -> None:
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        saved_actions = list(checkpoint["action_names"])
        if saved_actions != self.action_names:
            raise ValueError(
                "Checkpoint action space does not match current environment. "
                f"checkpoint={saved_actions}, current={self.action_names}"
            )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])


def run_random_rollout(env: MultiUavTaskEnv, seed: int | None = None) -> dict[str, float]:
    import random

    rng = random.Random(seed)
    env.reset()
    total_rewards = {agent_id: 0.0 for agent_id in env.agent_ids}
    done = False
    while not done:
        valid = env.valid_actions()
        actions = {
            agent_id: rng.choice(agent_actions)
            for agent_id, agent_actions in valid.items()
        }
        _, rewards, done, _ = env.step(actions)
        for agent_id, reward in rewards.items():
            total_rewards[agent_id] += reward
    return total_rewards
