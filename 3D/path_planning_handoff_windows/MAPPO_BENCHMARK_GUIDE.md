# MAPPO 训练与对比实验指南

本文档记录当前推荐的 MAPPO 实验流程，用于把训练后的 checkpoint 纳入 baseline / MARL greedy 对比表。

## 1. 训练 MAPPO checkpoint

默认读取 `configs/default.yaml` 中的 `marl` 与 `mappo` 配置：

```bash
python examples/run_mappo_train.py --config configs/default.yaml --output-dir outputs/mappo_train
```

关键输出：

```text
outputs/mappo_train/mappo_checkpoint.pt
outputs/mappo_train/best_checkpoint.pt
outputs/mappo_train/checkpoint_eval_history.csv
outputs/mappo_train/training_history.csv
outputs/mappo_train/training_summary.md
outputs/mappo_train/policy_eval.csv
outputs/mappo_train/best_policy_eval.csv
outputs/mappo_train/training_curves.png
```

当前默认训练稳定性设置：

```yaml
mappo:
  reward_scale: 0.01
  normalize_value_targets: true
  mask_wait_when_tasks_available: true
  eval_interval: 1
```

其中 `mask_wait_when_tasks_available` 表示：只要当前还有可执行任务，就不允许策略选择 `wait`，避免短训练模型学成空转策略。

## 2. 加载 checkpoint 单独评估

```bash
python examples/evaluate_mappo_policy.py ^
  --config configs/default.yaml ^
  --checkpoint outputs/mappo_train/mappo_checkpoint.pt ^
  --episodes 3 ^
  --output outputs/mappo_train/policy_eval_loaded.csv
```

评估指标会包含：

```text
mean_total_reward
mean_completed_task_count
mean_average_weather_cost
mean_total_path_cost
mean_total_distance_km
mean_conflict_count
mean_direct_action_count
mean_weather_grid_action_count
mean_weather_3d_action_count
```

这些指标用于判断 checkpoint 的任务完成能力、路径代价，以及模型实际偏向哪一种路线策略。

## 3. 与 baseline / MARL greedy 同表对比

```bash
python examples/run_mappo_benchmark.py ^
  --config configs/default.yaml ^
  --checkpoint outputs/mappo_train/mappo_checkpoint.pt ^
  --output-dir outputs/mappo_benchmark
```

关键输出：

```text
outputs/mappo_benchmark/metrics_with_mappo.csv
outputs/mappo_benchmark/comparison.md
outputs/mappo_benchmark/mappo_policy_eval.csv
outputs/mappo_benchmark/assignments_reference.csv
```

`comparison.md` 会把以下方法放在同一张表：

```text
one_shot
sequential
weather_grid
marl_greedy
mappo_checkpoint
```

注意：checkpoint 的 action space 必须与当前 `configs/default.yaml` 中的 `marl.route_strategies` 和 `marl.use_height_actions` 保持一致。如果改了动作空间，需要重新训练 checkpoint。

## 4. 批量 MAPPO 超参数实验

默认 suite：

```text
configs/mappo_experiments.yaml
```

运行：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_experiments.yaml
```

快速 smoke check：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_experiments.yaml --max-experiments 1
```

关键输出：

```text
outputs/mappo_experiments/mappo_experiment_summary.csv
outputs/mappo_experiments/mappo_experiment_summary.md
outputs/mappo_experiments/best_experiment.md
outputs/mappo_experiments/<experiment_name>/mappo_checkpoint.pt
outputs/mappo_experiments/<experiment_name>/best_checkpoint.pt
outputs/mappo_experiments/<experiment_name>/checkpoint_eval_history.csv
```

当前最佳实验选择规则：

```text
1. 优先完成任务数更多
2. 其次总奖励更高
3. 再其次总路径代价更低
```

选出的最佳 checkpoint 可以继续输入 `examples/run_mappo_benchmark.py`，与 baseline 和 MARL greedy 同表比较。

正式长训练 suite：

```text
configs/mappo_long_experiments.yaml
```

运行：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_long_experiments.yaml
```

长训练 suite 当前包含 `30 / 50 / 100` episode 三组实验，并通过 `eval_interval` 控制评估频率，避免每一轮都跑验证导致训练过慢。
