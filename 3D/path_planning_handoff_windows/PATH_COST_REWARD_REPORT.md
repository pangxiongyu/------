# Path Cost Reward 实验报告

本文档记录将 `total_path_cost` 直接纳入 MAPPO reward 后的实验结果。

## 1. 新增 Reward 项

当前 reward 已支持直接惩罚路径总代价：

```yaml
marl:
  reward:
    path_cost_weight: 0.0
    max_path_cost: 12000.0
```

代码入口：

```text
src/marl/reward.py
src/marl/env.py
src/marl/scenario_env.py
```

reward 形式：

```text
reward =
  task_complete_reward * priority
  - distance_weight * normalized_distance
  - weather_weight * weather_cost
  - energy_weight * energy_pressure
  - risk_weight * risk_penalty
  - path_cost_weight * normalized_path_cost
```

默认 `path_cost_weight: 0.0`，因此旧实验默认不受影响。

## 2. 单元测试

新增测试：

```text
tests/test_reward_config.py
```

验证内容：

```text
1. weather_weight 改变会改变环境 reward
2. path_cost_weight 改变会改变环境 reward
3. reward info 会导出 normalized_path_cost
```

当前测试结果：

```text
32 passed
```

## 3. Path Cost Sweep

配置：

```text
configs/mappo_pathcost_sweep.yaml
```

运行：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_pathcost_sweep.yaml
```

实验组：

```text
pathcost_w0_e20
pathcost_w50_e20
pathcost_w100_e20
```

20 episode 多场景验证 best path cost：

```text
pathcost_w0_e20   best_mean_total_path_cost = 8120.8657
pathcost_w50_e20  best_mean_total_path_cost = 7714.7085
pathcost_w100_e20 best_mean_total_path_cost = 7714.7085
```

结论：

```text
path_cost_weight 已经开始改善验证集 path cost。
```

## 4. Path Cost 长训

配置：

```text
configs/mappo_pathcost_long.yaml
```

运行：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_pathcost_long.yaml
```

实验组：

```text
pathcost_w50_e50
pathcost_w100_e50
```

训练最终 checkpoint 在默认场景上的表现：

```text
pathcost_w50_e50 final checkpoint:
mean_total_path_cost = 6738.1788
mean_total_reward = 425.3553
weather_3d_action_count = 4
```

对比此前结果：

```text
marl_greedy path cost:              7907.5821
multi-scenario selected path cost:  7038.4607
path-cost final checkpoint:         6738.1788
single-scenario long best:          6607.0977
weather_grid baseline:              5463.6228
```

## 5. 关键发现

`path_cost_weight` 有实际效果：

```text
验证集 best path cost: 8120.8657 -> 7714.7085
默认场景 final path cost: 7038.4607 -> 6738.1788
```

但是当前出现了一个重要分歧：

```text
验证集 best checkpoint: 7038.4607 default path cost
最终 checkpoint:        6738.1788 default path cost
```

说明当前验证集平均选择和默认场景最优并不完全一致。这不是 bug，而是训练目标从单场景优化转向多场景泛化后的正常现象。

## 6. 当前结论

工程上，第二步 reward 调权已经完成，并且 `path_cost_weight` 是有效方向。

科研上，下一轮应继续：

```text
1. 保留 path_cost_weight = 50 作为候选默认值。
2. 将 path-cost 长训扩展到更多 seed。
3. 增加验证场景数量，降低 checkpoint 选择偶然性。
4. 在最终报告中同时区分：
   - validation-selected checkpoint
   - final checkpoint
   - single-scenario best checkpoint
```

当前最推荐用于默认场景 benchmark 的 checkpoint：

```text
outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt
```

当前最推荐用于多场景泛化口径的 checkpoint：

```text
outputs/mappo_pathcost_long/pathcost_w50_e50/best_checkpoint.pt
```
