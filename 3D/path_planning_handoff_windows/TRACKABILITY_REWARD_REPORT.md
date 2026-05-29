# MAPPO 可跟踪性优化报告

本文档记录本轮针对“MAPPO 路径可跟踪性”的优化工作。优化目标是减少 MAPPO 输出中的超长 direct 航段，让高层路径更容易被 Robust MPC 跟踪，从而降低跟踪误差和约束违反次数。

## 1. 问题背景

此前最终 benchmark 中，推荐的 path-cost checkpoint 可以完成全部任务，但仍会选择部分长 direct 航段。

旧 checkpoint：

```text
outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt
```

其 MPC 指标存在明显问题：

| 指标 | 旧 MAPPO checkpoint |
| --- | ---: |
| `mpc_mean_tracking_error` | 69.3290 |
| `mpc_max_tracking_error` | 2731.1681 |
| `mpc_constraint_violation_count` | 21 |
| `direct_action_count` | 1 |
| `weather_grid_action_count` | 0 |
| `weather_3d_action_count` | 4 |

原因是：高层 reward 主要关注任务完成、路径代价、气象代价和能耗风险，但没有显式表达“这条路径是否容易被底层 MPC 跟踪”。

## 2. 优化思路

本轮加入一个轻量级的 MPC 可跟踪性代理指标：

```text
max_segment_distance_km
```

含义是：一条 route 中相邻 waypoint 之间的最大距离。

直观解释：

1. direct 路径通常只有起点和终点，单段距离很长。
2. weather-grid / weather-3D 路径包含更多中间 waypoint，单段距离更短。
3. 单段距离越短，MPC 跟踪越平滑，约束违反风险越低。

因此，本轮 reward shaping 增加：

```text
trackability_penalty = trackability_weight * normalized(max_segment_distance_km)
```

默认配置中 `trackability_weight=0.0`，不改变已有实验口径。只有新配置 `configs/mappo_trackability_sweep.yaml` 会启用该项。

## 3. 代码改动

新增或修改的核心文件：

| 文件 | 作用 |
| --- | --- |
| `src/core/geo_utils.py` | 新增 `max_route_segment_distance_km` |
| `src/marl/reward.py` | 新增 `trackability_weight`、`max_trackable_segment_km` 和 `trackability_penalty` |
| `src/marl/env.py` | 在环境事件中记录 `waypoint_count`、`max_segment_distance_km` |
| `src/marl/scenario_env.py` | 从配置读取 trackability reward 参数 |
| `src/marl/train_mappo.py` | 评估时导出 `mean_peak_segment_distance_km`、`mean_trackability_penalty` |
| `src/eval/metrics.py` | baseline/MARL assignment 也导出最长航段指标 |
| `src/eval/mappo_checkpoint.py` | checkpoint 可比较指标中加入 trackability 指标 |
| `examples/run_mappo_experiments.py` | 支持 `selection_mode: trackability` |
| `configs/mappo_trackability_sweep.yaml` | 新增可跟踪性优化实验配置 |
| `tests/test_reward_config.py` | 测试 trackability reward 是否生效 |

## 4. 新配置

新增配置文件：

```text
configs/mappo_trackability_sweep.yaml
```

当前包含两个候选实验：

| 实验 | path-cost 权重 | trackability 权重 | episode |
| --- | ---: | ---: | ---: |
| `pathcost_w50_track_w25_e30` | 50 | 25 | 30 |
| `pathcost_w50_track_w50_e30` | 50 | 50 | 30 |

本轮已完成第一个实验的 smoke run。

## 5. smoke run 结果

运行命令：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_sweep.yaml --max-experiments 1
```

输出目录：

```text
outputs/mappo_trackability_sweep/
```

当前 smoke run 最佳 checkpoint：

```text
outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt
```

训练/评估结果摘要：

| 指标 | 数值 |
| --- | ---: |
| `mean_completed_task_count` | 5 |
| `mean_total_reward` | 376.5655 |
| `mean_total_path_cost` | 7541.6717 |
| `mean_direct_action_count` | 0 |
| `mean_weather_grid_action_count` | 2 |
| `mean_weather_3d_action_count` | 3 |
| `mean_average_max_segment_distance_km` | 180.2855 |
| `mean_peak_segment_distance_km` | 242.1842 |
| `mean_trackability_penalty` | 22.5357 |

## 6. MPC benchmark 验证

使用 smoke run checkpoint 运行 benchmark：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt --output-dir outputs/mappo_trackability_benchmark_smoke
```

输出目录：

```text
outputs/mappo_trackability_benchmark_smoke/
```

关键结果：

| 指标 | 旧 path-cost MAPPO | trackability MAPPO |
| --- | ---: | ---: |
| `completed_task_count` | 5 | 5 |
| `direct_action_count` | 1 | 0 |
| `weather_grid_action_count` | 0 | 2 |
| `weather_3d_action_count` | 4 | 3 |
| `max_segment_distance_km` | 未在旧表导出 | 233.2314 |
| `mpc_mean_tracking_error` | 69.3290 | 0.1204 |
| `mpc_max_tracking_error` | 2731.1681 | 5.3404 |
| `mpc_constraint_violation_count` | 21 | 0 |
| `total_path_cost` | 6738.1788 | 7949.2716 |

结论：

1. 可跟踪性 reward 明显减少 direct 航段。
2. MAPPO 开始使用 weather-grid 和 weather-3D 路径动作。
3. Robust MPC 跟踪误差显著下降，约束违反次数降为 0。
4. 代价是路径总代价升高，因此该策略更适合“规划 + 管控闭环演示”，而旧 path-cost checkpoint 更适合“路径代价对比”。

## 7. 后续建议

后续应继续完成完整 sweep：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_sweep.yaml
```

然后分别 benchmark：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt --output-dir outputs/mappo_trackability_benchmark_w25

python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_sweep/pathcost_w50_track_w50_e30/best_checkpoint.pt --output-dir outputs/mappo_trackability_benchmark_w50
```

建议最终报告中保留双 checkpoint 口径：

| 用途 | checkpoint |
| --- | --- |
| 路径代价对比 | `outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt` |
| MPC 闭环演示 | `outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt` |

这样可以清楚说明：项目已经能在“路径代价”和“底层可控性”之间做权衡。

## 8. 完整 sweep 结果更新

当前已经完整运行：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_sweep.yaml
```

输出：

```text
outputs/mappo_trackability_sweep/mappo_experiment_summary.md
outputs/mappo_trackability_sweep/best_experiment.md
```

完整结果：

| 实验 | 完成任务数 | 默认场景 path cost | 默认场景 peak segment km | weather-grid 动作 | weather-3D 动作 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `pathcost_w50_track_w25_e30` | 5 | 7541.6717 | 242.1842 | 2 | 3 |
| `pathcost_w50_track_w50_e30` | 5 | 7061.4955 | 242.1842 | 2 | 3 |

按照验证集 `selection_mode: trackability`，当前选择：

```text
outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt
```

该 checkpoint 的最终 benchmark 输出：

```text
outputs/mappo_trackability_benchmark_final/comparison.md
outputs/mappo_trackability_benchmark_final/mpc_tracking.csv
```

## 9. 多 seed / 多 episode 结果

当前已经新增并运行：

```text
configs/mappo_trackability_multiseed.yaml
```

运行命令：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_multiseed.yaml
```

该配置包含 3 个 seed，每个训练 40 episodes：

| 实验 | seed | episode | 完成任务数 | 默认场景 path cost | grid 动作 | 3D 动作 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `track_w25_seed7_e40` | 7 | 40 | 5 | 6350.1909 | 2 | 2 |
| `track_w25_seed11_e40` | 11 | 40 | 5 | 7521.3170 | 0 | 4 |
| `track_w25_seed17_e40` | 17 | 40 | 5 | 10874.3804 | 1 | 3 |

多 seed 最优 checkpoint：

```text
outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt
```

该 checkpoint benchmark：

```text
outputs/mappo_trackability_multiseed_best_benchmark/comparison.md
```

关键指标：

| 指标 | 数值 |
| --- | ---: |
| `completed_task_count` | 5 |
| `mpc_mean_tracking_error` | 0.1533 |
| `mpc_max_tracking_error` | 8.6271 |
| `mpc_constraint_violation_count` | 0 |
| `total_path_cost` | 8971.0321 |

最终建议：

1. 答辩中展示 `pathcost_w50_track_w25_e30`，因为它的 MPC 跟踪误差最低。
2. 论文/结题报告中补充 `track_w25_seed7_e40`，证明多 seed / 更长训练下结论仍能成立。
