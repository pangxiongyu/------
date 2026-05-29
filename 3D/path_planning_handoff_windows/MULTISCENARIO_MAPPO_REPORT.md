# 多场景 MAPPO 选模报告

本文档记录“按验证场景集合选择 best checkpoint”的实现和实验结果。

## 1. 新增能力

MAPPO trainer 现在支持在训练中使用多个验证场景评估 checkpoint：

```text
src/marl/train_mappo.py
```

新增能力：

```text
evaluate_policy_across_envs()
aggregate_policy_metrics()
train_with_eval_checkpoints(..., eval_env_factories=...)
```

checkpoint 选择支持两种模式：

```text
reward:    先任务完成数，再总奖励，再路径代价
path_cost: 先任务完成数，再路径代价，再总奖励
```

## 2. 验证场景集合

验证集配置：

```text
configs/mappo_validation_same_action.yaml
```

该验证集保持同一动作空间：

```text
uav_count: 3
task_count: 5
task_id: T1-T5
route_strategies: direct / weather_grid / weather_3d
```

变化维度：

```text
time_index: 0 / 12 / 18
height_m: 10 / 100
```

这样可以保证同一个 checkpoint 能在多个气象场景上公平评估。

## 3. 多场景 MAPPO 实验

配置：

```text
configs/mappo_multiscenario_experiments.yaml
```

运行命令：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_multiscenario_experiments.yaml
```

输出目录：

```text
outputs/mappo_multiscenario_experiments/
```

当前实验组：

```text
balanced_multival_e20
path_focused_multival_e20
weather_focused_multival_e20
```

选择模式：

```yaml
selection_mode: path_cost
```

## 4. 当前最佳多场景模型

当前最佳：

```text
experiment: balanced_multival_e20
best_eval_episode: 15
validation_scenario_count: 4
mean_completed_task_count: 5
mean_total_reward: 407.1317
mean_total_path_cost: 8120.8657
mean_weather_grid_action_count: 0
mean_weather_3d_action_count: 2
```

最佳 checkpoint：

```text
outputs/mappo_multiscenario_experiments/balanced_multival_e20/best_checkpoint.pt
```

## 5. 默认场景 Benchmark

使用多场景最佳 checkpoint 回到默认场景测试：

```bash
python examples/run_mappo_benchmark.py ^
  --config configs/default.yaml ^
  --checkpoint outputs/mappo_multiscenario_experiments/balanced_multival_e20/best_checkpoint.pt ^
  --output-dir outputs/mappo_multiscenario_benchmark
```

输出：

```text
outputs/mappo_multiscenario_benchmark/comparison.md
outputs/mappo_multiscenario_benchmark/metrics_with_mappo.csv
```

默认场景结果：

| method | completed_task_count | total_reward | total_path_cost | total_distance_km | weather_3d_action_count |
| --- | ---: | ---: | ---: | ---: | ---: |
| weather_grid | 5 | 0.0000 | 5463.6228 | 5139.0705 | 0 |
| marl_greedy | 5 | 431.4538 | 7907.5821 | 7518.3410 | 0 |
| mappo_multiscenario | 5 | 415.5912 | 7038.4607 | 6898.2125 | 2 |

## 6. 结论

多场景选模后，MAPPO 在默认场景上仍然优于 `marl_greedy`：

```text
marl_greedy path cost: 7907.5821
mappo_multiscenario path cost: 7038.4607
```

但它弱于单场景长训练 best checkpoint：

```text
single-scenario long best path cost: 6607.0977
multi-scenario selected path cost: 7038.4607
```

这符合预期：单场景模型更会贴合默认场景，多场景模型更保守，泛化口径更可靠。

当前仍未超过强 baseline：

```text
weather_grid path cost: 5463.6228
mappo_multiscenario path cost: 7038.4607
```

## 7. 下一步

下一轮建议：

```text
1. 把多场景训练从 20 episode 提升到 50/100 episode。
2. 将 validation_scenario_count 从 4 扩展到更多同动作空间场景。
3. 增加 path_cost 直接归一化惩罚项，而不只依赖 distance/weather 两个代理项。
4. 为 8 任务生成场景单独训练一个更大 action space 的 MAPPO 模型。
```
