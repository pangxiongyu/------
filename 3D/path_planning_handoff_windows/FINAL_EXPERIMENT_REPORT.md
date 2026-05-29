# 最终实验报告

本文档记录当前项目阶段的最终可复现实验结果。

## 1. 当前完成状态

项目当前已经完成以下链路：

```text
气象地图 + UAV 动态画像 + 任务点
-> baseline / MARL greedy / MAPPO 任务分配与路径策略
-> weather_grid / weather_3d 气象路径代价评估
-> Robust MPC 路线跟踪
-> 批量实验、训练摘要、best checkpoint 选择、最终 benchmark
```

## 2. 长训练 MAPPO 实验

运行命令：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_long_experiments.yaml
```

输出目录：

```text
outputs/mappo_long_experiments/
```

长训练 suite 包含：

```text
seed11_e30_lr3e4
seed11_e50_lr3e4
seed11_e100_lr1e4
```

当前最佳实验：

```text
experiment: seed11_e50_lr3e4
best_eval_episode: 45
mean_completed_task_count: 5
mean_total_reward: 421.0793
mean_total_path_cost: 6607.0977
mean_weather_grid_action_count: 0
mean_weather_3d_action_count: 3
```

最佳 checkpoint：

```text
outputs/mappo_long_experiments/seed11_e50_lr3e4/best_checkpoint.pt
```

## 3. 最终 benchmark

运行命令：

```bash
python examples/run_mappo_benchmark.py ^
  --config configs/default.yaml ^
  --checkpoint outputs/mappo_long_experiments/seed11_e50_lr3e4/best_checkpoint.pt ^
  --output-dir outputs/mappo_final_benchmark
```

关键输出：

```text
outputs/mappo_final_benchmark/comparison.md
outputs/mappo_final_benchmark/metrics_with_mappo.csv
outputs/mappo_final_benchmark/mappo_policy_eval.csv
```

## 4. 关键指标对比

| method | completed_task_count | total_reward | total_path_cost | total_distance_km | average_weather_cost | weather_grid_action_count | weather_3d_action_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| one_shot | 3 | 0.0000 | 4826.7788 | 4825.2952 | 0.4945 | 0 | 0 |
| sequential | 5 | 0.0000 | 5848.3320 | 5845.9233 | 0.4817 | 0 | 0 |
| weather_grid | 5 | 0.0000 | 5463.6228 | 5139.0705 | 0.3938 | 0 | 0 |
| marl_greedy | 5 | 431.4538 | 7907.5821 | 7518.3410 | 0.3406 | 5 | 0 |
| mappo_checkpoint | 5 | 421.0793 | 6607.0977 | 6502.8598 | 0.4802 | 0 | 3 |

## 5. 结论

当前 MAPPO 长训练 best checkpoint 已经明显优于短训练 checkpoint：

```text
短训练 best path cost: 8140.7223
长训练 best path cost: 6607.0977
```

相较于 `marl_greedy`：

```text
marl_greedy path cost: 7907.5821
mappo_checkpoint path cost: 6607.0977
```

说明 MAPPO 已经开始学到更优的联合匹配结果，并且会主动使用 `weather_3d` 路径策略。

但它仍未超过 `weather_grid` baseline 的路径代价：

```text
weather_grid path cost: 5463.6228
mappo_checkpoint path cost: 6607.0977
```

因此当前阶段的定位是：

```text
工程链路完整可复现，MAPPO 已有有效改进，但还需要更大规模训练与奖励权重调优，才能稳定超过强 baseline。
```

## 6. 后续建议

下一阶段优先做三件事：

```text
1. 把 MAPPO 训练扩展到更多任务点和更多 UAV，避免只在 5 任务小场景中过拟合。
2. 调整 reward 中距离、气象、能耗、风险的权重，让 path cost 与训练目标更一致。
3. 增加多时间片和多气象高度层的验证集，避免只在默认 t0/h10 场景上选模型。
```
