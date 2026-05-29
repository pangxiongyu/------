# 基于 MARL 与 Robust MPC 的无人机联合路径规划与管控平台结题报告

## 摘要

本项目面向复杂气象环境下的无人机任务分配、路径规划与底层航迹跟踪问题，构建了一个结合三维气象地图、无人机个体画像、多智能体强化学习和 Robust MPC 的联合规划与管控原型系统。

项目已完成从数据读取、任务构建、baseline 对比、MARL/MAPPO 训练、path-cost reward 优化、Robust MPC 跟踪评估，到最终 benchmark 与报告导出的完整闭环。进一步地，项目针对 MAPPO 生成路径中存在的长 direct 航段问题，引入了可跟踪性 reward，使高层规划结果更容易被底层 MPC 控制器稳定跟踪。

最终系统能够展示两个核心能力：

1. 使用 MARL/MAPPO 完成“气象-能力”约束下的任务分配与路径策略学习。
2. 使用 Robust MPC 评估和管控高层路径的底层可跟踪性，实现“规划 + 控制”闭环。

## 1. 研究背景与问题定义

传统无人机路径规划方法通常依赖离线规则或静态最短路，在面对突变气象、不同无人机健康状态、任务优先级和多机协同冲突时，响应能力有限。

本项目关注的问题是：

```text
给定无人机个体画像、任务点、载荷需求和三维气象代价地图，
如何为多架无人机分配任务并生成可执行路径，
同时保证路径在底层控制中具有较好的可跟踪性？
```

该问题包含三层约束：

1. 任务层：任务完成率、任务优先级、载荷约束。
2. 路径层：距离、气象风险、路径总代价。
3. 控制层：MPC 跟踪误差、控制能耗、约束违反次数。

## 2. 系统总体架构

系统采用分层式结构：

```text
数据输入
  -> 三维气象地图 + UAV 个体画像 + 任务需求
  -> baseline / MARL / MAPPO 高层规划
  -> Robust MPC 底层航迹跟踪
  -> 指标评估、图表输出、报告导出
```

核心目录：

| 模块 | 目录 | 作用 |
| --- | --- | --- |
| 数据层 | `data/` | UAV profiles、任务点、气象代价地图 |
| 配置层 | `configs/` | 控制场景、reward、训练参数、输出目录 |
| 基础计算 | `src/core/` | 地理距离、路径代价、数据结构 |
| 数据读取 | `src/data_io/` | 读取配置并组装 PlanningScenario |
| baseline | `src/baseline/` | one_shot、sequential、weather-aware baseline |
| 路径规划 | `src/planning/` | weather-grid、weather-3D 路径规划 |
| MARL/MAPPO | `src/marl/` | 环境、动作空间、reward、MAPPO 训练 |
| Robust MPC | `src/mpc/` | QP 控制器、风扰动、路径跟踪 |
| 评估导出 | `src/eval/` | benchmark、checkpoint、MPC 指标、报告 |

## 3. 数据与个体画像

项目输入数据包括：

| 数据 | 文件或目录 | 说明 |
| --- | --- | --- |
| UAV 个体画像 | `data/uav_profiles/` | 包含 MAMBA-Lite/Torch MAMBA 动态画像 |
| 任务点 | `data/tasks/demo_tasks.csv` | 默认任务位置、载荷和优先级 |
| 气象地图 | `data/weather_cost_map/` | 24 小时、多高度气象代价地图 |
| 原始气象数据 | `output_data/` | 多地区、多时间段 CSV 数据 |

当前 MAMBA-Lite 画像已经可作为 MARL 状态输入使用，但它仍属于非正式 MAMBA 版本，后续可进一步替换为更完整的画像模型。

## 4. 方法设计

### 4.1 baseline 方法

项目实现了以下 baseline：

| 方法 | 说明 |
| --- | --- |
| `one_shot` | 每架 UAV 至多接一个任务 |
| `sequential` | 顺序贪心分配，可连续执行多个任务 |
| `weather_grid` | 结合二维气象网格进行路径规划 |
| `marl_greedy` | 基于 MARL 环境和贪心策略的对照方法 |

这些方法用于和 MAPPO 训练策略进行对比。

### 4.2 MAPPO 高层策略

MAPPO 策略负责选择：

1. 哪架无人机执行哪个任务。
2. 是否使用 direct、weather-grid 或 weather-3D 路径。
3. 在启用高度动作时选择目标高度。

状态输入包括 UAV 位置、高度、健康评分、风险等级、最近任务距离、气象代价、剩余任务数量等。

### 4.3 path-cost reward

早期训练中出现 `value_loss` 数值过大的问题，原因是 reward/return 中包含真实路径代价，尺度过大。

项目已加入：

```text
reward_scale
value_target_normalization
path_cost_weight
max_path_cost
```

该修复降低了 critic 数值不稳定风险。

### 4.4 trackability reward

为了让 MAPPO 输出的路径更容易被 MPC 跟踪，项目新增可跟踪性代理指标：

```text
max_segment_distance_km
```

该指标表示一条 route 中相邻 waypoint 之间的最大距离。长 direct 航段通常该值很大，而 weather-grid/weather-3D 路径由于有更多中间 waypoint，因此更适合 MPC 跟踪。

新增 reward 项：

```text
trackability_penalty = trackability_weight * normalized(max_segment_distance_km)
```

该项默认关闭，启用配置位于：

```text
configs/mappo_trackability_sweep.yaml
configs/mappo_trackability_multiseed.yaml
```

### 4.5 Robust MPC

Robust MPC 用于评估高层路径是否容易被底层控制器跟踪。输出指标包括：

| 指标 | 含义 |
| --- | --- |
| `mpc_mean_tracking_error` | 平均跟踪误差 |
| `mpc_max_tracking_error` | 最大跟踪误差 |
| `mpc_total_control_effort` | 控制能耗近似量 |
| `mpc_constraint_violation_count` | 高度、速度、加速度约束违反次数 |
| `mpc_tracked_route_count` | 成功跟踪的 route 数 |

## 5. 实验设置

主要实验配置：

| 实验 | 配置文件 | 输出目录 |
| --- | --- | --- |
| 默认 baseline | `configs/default.yaml` | `outputs/default_scenario/` |
| 多场景 baseline | `configs/validation_scenarios.yaml` | `outputs/validation_scenarios/` |
| path-cost MAPPO | `configs/mappo_pathcost_long.yaml` | `outputs/mappo_pathcost_long/` |
| trackability sweep | `configs/mappo_trackability_sweep.yaml` | `outputs/mappo_trackability_sweep/` |
| 多 seed 稳健性 | `configs/mappo_trackability_multiseed.yaml` | `outputs/mappo_trackability_multiseed/` |

最终主要 checkpoint：

| 用途 | checkpoint |
| --- | --- |
| 路径代价对比 | `outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt` |
| MPC 闭环演示 | `outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt` |
| 多 seed 最优 | `outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt` |

## 6. 实验结果

### 6.1 默认场景高层规划结果

path-cost MAPPO benchmark：

```text
outputs/mappo_pathcost_benchmark_final/comparison.md
```

| 方法 | 完成任务数 | 总距离 km | 总路径代价 | 总奖励 |
| --- | ---: | ---: | ---: | ---: |
| one_shot | 3 | 4825.2952 | 4826.7788 | 0 |
| sequential | 5 | 5845.9233 | 5848.3320 | 0 |
| weather_grid | 5 | 5139.0705 | 5463.6228 | 0 |
| marl_greedy | 5 | 7518.3410 | 7907.5821 | 431.4538 |
| path-cost MAPPO | 5 | 6584.3751 | 6738.1788 | 425.3553 |

结论：path-cost MAPPO 能完成全部任务，并且路径代价低于 `marl_greedy`，但仍未超过强 baseline `weather_grid`。

### 6.2 MPC 闭环结果对比

| 指标 | path-cost MAPPO | trackability MAPPO |
| --- | ---: | ---: |
| `completed_task_count` | 5 | 5 |
| `direct_action_count` | 1 | 0 |
| `weather_grid_action_count` | 0 | 2 |
| `weather_3d_action_count` | 4 | 3 |
| `mpc_mean_tracking_error` | 69.3290 | 0.1204 |
| `mpc_max_tracking_error` | 2731.1681 | 5.3404 |
| `mpc_constraint_violation_count` | 21 | 0 |
| `total_path_cost` | 6738.1788 | 7949.2716 |

结论：trackability reward 明显改善 MPC 可跟踪性，但路径总代价上升，体现了“路径效率”和“底层可控性”之间的权衡。

### 6.3 trackability sweep 结果

完整 sweep 输出：

```text
outputs/mappo_trackability_sweep/mappo_experiment_summary.md
```

| 实验 | 完成任务数 | 路径代价 | peak segment km | grid 动作 | 3D 动作 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `track_w25_e30` | 5 | 7541.6717 | 242.1842 | 2 | 3 |
| `track_w50_e30` | 5 | 7061.4955 | 242.1842 | 2 | 3 |

按验证集 `selection_mode: trackability` 选择，当前最佳为：

```text
outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt
```

### 6.4 多 seed / 多 episode 稳健性实验

多 seed 配置：

```text
configs/mappo_trackability_multiseed.yaml
```

输出：

```text
outputs/mappo_trackability_multiseed/mappo_experiment_summary.md
```

| 实验 | seed | episode | 完成任务数 | 路径代价 | direct 动作 | grid 动作 | 3D 动作 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `track_w25_seed7_e40` | 7 | 40 | 5 | 6350.1909 | 1 | 2 | 2 |
| `track_w25_seed11_e40` | 11 | 40 | 5 | 7521.3170 | 1 | 0 | 4 |
| `track_w25_seed17_e40` | 17 | 40 | 5 | 10874.3804 | 1 | 1 | 3 |

按验证集 trackability 选择的多 seed 最优：

```text
outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt
```

其最终 benchmark：

```text
outputs/mappo_trackability_multiseed_best_benchmark/comparison.md
```

关键 MPC 指标：

| 指标 | 数值 |
| --- | ---: |
| `completed_task_count` | 5 |
| `mpc_mean_tracking_error` | 0.1533 |
| `mpc_max_tracking_error` | 8.6271 |
| `mpc_constraint_violation_count` | 0 |
| `total_path_cost` | 8971.0321 |

结论：多 seed 结果显示 trackability reward 能稳定维持任务完成，并在最优 seed 中保持 MPC 约束违反为 0。

## 7. 创新点总结

本项目的主要创新点可以归纳为：

1. 将 UAV 个体画像、三维气象地图和任务需求统一进 MARL 状态与 reward。
2. 将 MAPPO 用于多 UAV 任务分配与路径策略选择。
3. 将 weather-grid/weather-3D 路径动作纳入强化学习动作空间。
4. 将 Robust MPC 指标并入最终 benchmark，形成“规划 + 控制”闭环评估。
5. 新增 trackability reward，使高层策略开始关注底层控制可执行性。

## 8. 局限与后续工作

当前系统仍有以下局限：

1. MAPPO 仍未在路径代价上超过 `weather_grid` 强 baseline。
2. trackability reward 会提升 MPC 跟踪性能，但可能增加路径代价。
3. 当前训练规模仍有限，正式论文级实验应继续扩大 seed、episode 和场景数量。
4. MAMBA-Lite 画像仍可进一步替换为更正式的 MAMBA 模型。
5. 还可以引入 imitation learning，让 MAPPO 先学习 weather-grid 专家策略。

后续建议：

1. 扩大多场景、多 seed 训练。
2. 设计联合目标：同时最小化 path cost 和 MPC tracking error。
3. 将 MPC 真实跟踪误差作为离线 reward 或后验筛选指标。
4. 增加 4 UAV / 8 task、6 UAV / 12 task 等大规模实验。

## 9. 结论

本项目已经完成可运行、可复现、可展示的无人机联合路径规划与管控原型。系统证明了：

1. MARL/MAPPO 可以完成多无人机任务分配与路径动作选择。
2. 三维气象路径和个体画像可以进入统一决策链路。
3. Robust MPC 可以作为底层控制闭环评价高层路径质量。
4. 通过 trackability reward，可以显著降低 MAPPO 路径的 MPC 跟踪误差和约束违反次数。

最终可以在答辩中强调：

```text
本项目不仅完成了路径规划，还把“路径是否可被控制器稳定执行”纳入了评价与优化，
形成了从个体画像、气象地图、MARL 分配到 Robust MPC 跟踪的完整闭环。
```
