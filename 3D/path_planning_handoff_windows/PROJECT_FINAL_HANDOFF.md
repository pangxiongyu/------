# UAV 路径规划项目最终交接报告

本文档用于集中说明当前项目状态、已完成模块、推荐 checkpoint、最终实验结论和后续任务。新成员建议先阅读 `README.md`，再阅读本文档、`PROJECT_FILE_RELATIONSHIP_GUIDE.md`、`REPRODUCIBLE_EXPERIMENT_COMMANDS.md` 和 `TRACKABILITY_REWARD_REPORT.md`。

## 1. 项目目标

本项目面向“基于 MARL 与 Robust MPC 的联合规划与管控平台”，目标是结合三维气象地图、无人机个体画像和任务需求，完成任务分配、路径规划和底层抗扰动航迹跟踪。

总体技术路线：

1. 使用已有 MAMBA/MAMBA-Lite 个体画像作为无人机能力输入。
2. 使用三维气象地图刻画空间、时间和高度上的风险/代价。
3. 使用 MARL/MAPPO 进行全局任务分配与路径策略学习。
4. 使用 Robust MPC 对高层路径进行底层抗扰动跟踪。
5. 使用统一 benchmark 输出任务完成率、路径代价、奖励、MPC 跟踪误差、控制能耗和约束违反次数。

## 2. 当前完成状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 数据读取与场景构建 | 已完成 | 支持 UAV profile、task、weather map 读取，并构建默认/验证场景 |
| MAMBA-Lite 画像接入 | 已完成 | 当前作为能力画像输入使用，后续可替换为正式 MAMBA |
| 基线规划器 | 已完成 | one_shot、sequential、weather_grid、marl_greedy 均可运行 |
| 二维/三维气象路径规划 | 已完成 | 支持 weather-grid 与 weather-3D 路径动作 |
| MARL 环境 | 已完成 | 支持任务分配、动作掩码、奖励计算、场景配置 |
| MAPPO 原型 | 已完成 | 支持训练、评估、checkpoint 保存和训练历史导出 |
| 奖励归一化修复 | 已完成 | 加入 reward scale、value target normalization、path-cost reward |
| MAPPO 可跟踪性优化 | 已完成 smoke 验证 | 加入 trackability reward，减少长 direct 航段对 MPC 的影响 |
| Robust MPC | 已完成并入 benchmark | 支持 QP/原型控制器，输出跟踪误差、控制能耗、约束违反次数 |
| 实验套件 | 已完成 | 支持 batch baseline、MAPPO sweep、多场景验证、最终 benchmark |
| 报告导出 | 已完成 | 已生成阶段报告、交接文档和复现实验命令清单 |

## 3. 推荐 checkpoint

建议保留两个主展示口径：

| 用途 | 推荐 checkpoint | 说明 |
| --- | --- | --- |
| 路径代价对比 | `outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt` | 路径代价较低，适合和 baseline 比较规划效率 |
| MPC 闭环演示 | `outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt` | 可跟踪性 reward smoke run，MPC 约束违反次数降为 0 |
| 多 seed 稳健性 | `outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt` | 3 seed × 40 episodes 中按 trackability 选择的最佳 checkpoint |
| 多场景泛化验证 | `outputs/mappo_pathcost_long/pathcost_w50_e50/best_checkpoint.pt` | 按 path cost 选择的验证集最佳模型 |
| 单默认场景历史最优参考 | `outputs/mappo_long_experiments/seed11_e50_lr3e4/best_checkpoint.pt` | 默认场景 path cost 更低，但泛化口径不如 path-cost 套件明确 |

## 4. 关键实验结果

### 4.1 path-cost MAPPO

默认场景 benchmark：

```text
outputs/mappo_pathcost_benchmark_final/comparison.md
```

| 方法 | 完成任务数 | 总距离 km | 总路径代价 | 总奖励 | 说明 |
| --- | ---: | ---: | ---: | ---: | --- |
| one_shot | 3 | 4825.2952 | 4826.7788 | 0 | 路径短但只完成 3 个任务 |
| sequential | 5 | 5845.9233 | 5848.3320 | 0 | 简单可行基线 |
| weather_grid | 5 | 5139.0705 | 5463.6228 | 0 | 当前默认场景路径代价最佳基线 |
| marl_greedy | 5 | 7518.3410 | 7907.5821 | 431.4538 | 贪心 MARL baseline |
| mappo_checkpoint | 5 | 6584.3751 | 6738.1788 | 425.3553 | path-cost MAPPO |

该 checkpoint 完成全部任务，并且比 `marl_greedy` 路径代价更低，但 MPC 跟踪仍存在长 direct 航段带来的误差。

### 4.2 Robust MPC 指标

path-cost MAPPO 的 MPC 指标：

| 指标 | 数值 |
| --- | ---: |
| `mpc_mean_tracking_error` | 69.3290 |
| `mpc_max_tracking_error` | 2731.1681 |
| `mpc_constraint_violation_count` | 21 |

### 4.3 trackability MAPPO

trackability smoke benchmark：

```text
outputs/mappo_trackability_benchmark_smoke/comparison.md
```

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

结论：可跟踪性 reward 明显改善 MPC 闭环表现，但会牺牲一部分路径代价。最终展示时建议同时保留这两个口径，说明系统可以在“路径代价”和“底层可控性”之间权衡。

## 5. 已解决的关键问题

### 5.1 value loss 数值爆炸

此前训练中 `value_loss` 达到 10000 以上，主要原因是 reward/return 直接使用真实物理路径代价，数值尺度过大。现在已经通过以下方式缓解：

1. `reward_scale`：降低进入 critic 的回报尺度。
2. `value_target_normalization`：对价值目标做标准化。
3. `path_cost_weight` 与 `max_path_cost`：把路径代价变成可控归一化惩罚。

相关代码：

```text
src/marl/reward.py
src/marl/env.py
src/marl/scenario_env.py
src/marl/train_mappo.py
```

### 5.2 Robust MPC 并入最终 benchmark

当前已经新增：

```text
src/eval/mpc_eval.py
tests/test_mpc_eval.py
outputs/mappo_pathcost_benchmark_final/mpc_tracking.csv
```

`examples/run_mappo_benchmark.py` 现在默认会输出 `mpc_*` 指标，并将每条 route 的跟踪结果写入 `mpc_tracking.csv`。

### 5.3 MAPPO 可跟踪性 reward

当前已新增：

```text
trackability_penalty = trackability_weight * normalized(max_segment_distance_km)
```

对应配置：

```text
configs/mappo_trackability_sweep.yaml
```

详细记录见：

```text
TRACKABILITY_REWARD_REPORT.md
```

## 6. 当前局限

当前项目已经形成完整可运行闭环，但仍有几个需要继续增强的点：

1. `weather_grid` 仍是默认场景路径代价最强 baseline，MAPPO 需要继续增强。
2. path-cost MAPPO 路径代价较优，但 MPC 跟踪不够稳。
3. trackability MAPPO 跟踪很稳，但路径代价会上升。
4. MAPPO 训练 episode 数仍偏少，正式实验建议做多 seed、多 episode、多场景训练。
5. 当前 MAMBA-Lite 画像可用，但不是正式 MAMBA，后续可替换或完善画像模块。

## 7. 下一阶段任务清单

建议后续按下面顺序继续：

1. 在更多场景上 benchmark 多 seed 最优 checkpoint。
2. 扩展 MAPPO 训练规模，增加 seed、episode 和任务规模。
3. 探索 combined selection：同时考虑 `path_cost`、`max_segment_distance_km` 和 `mpc_constraint_violation_count`。
4. 将 `weather_grid` 作为专家基线，尝试 imitation pretrain 或 reward shaping。
5. 替换或完善正式 MAMBA 个体画像，并确认画像字段与 MARL 状态输入一致。
6. 固化最终答辩实验：默认场景、突变气象场景、多高度场景、大规模任务场景。

## 8. 当前交付物

核心交付物包括：

```text
PROJECT_FILE_RELATIONSHIP_GUIDE.md
PROJECT_FINAL_HANDOFF.md
REPRODUCIBLE_EXPERIMENT_COMMANDS.md
TRACKABILITY_REWARD_REPORT.md
FINAL_DEFENSE_REPORT.md
DEFENSE_PRESENTATION_OUTLINE.md
UAV_MARL_MPC_DEFENSE_DECK.pptx
MARL_MPC_TASK_GUIDE.md
DEVELOPMENT_RUNBOOK.md
MAPPO_BENCHMARK_GUIDE.md
FINAL_EXPERIMENT_REPORT.md
SCENARIO_REWARD_TUNING_REPORT.md
MULTISCENARIO_MAPPO_REPORT.md
PATH_COST_REWARD_REPORT.md
```

当前项目已经具备：

```text
数据输入 -> 高层规划 -> MAPPO 训练/评估 -> Robust MPC 跟踪 -> 统一 benchmark -> 报告交接
```
