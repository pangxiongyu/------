# UAV 路径规划项目文档导航

本文档是项目根目录 Markdown 文档的总入口。新同学接手时，不需要把所有 `.md` 从头读一遍；按本文档的顺序阅读即可。

## 1. 一句话理解项目

本项目已经形成一个可运行的大创原型：

```text
UAV 个体画像 + 三维气象地图 + 任务数据
    -> MARL/MAPPO 高层任务分配与路径策略选择
    -> Robust MPC 底层航迹跟踪
    -> 统一 benchmark、实验报告和答辩材料
```

当前项目重点不是单纯“找一条最短路径”，而是同时回答三个问题：

1. 哪架 UAV 执行哪个任务？
2. 在气象约束下走哪种路径？
3. 这条路径能否被底层控制器稳定跟踪？

## 2. 新人最短阅读路线

如果你是第一次接手项目，按下面顺序读。

| 顺序 | 文档 | 目的 |
| --- | --- | --- |
| 1 | `README.md` | 当前文档，先建立全局地图 |
| 2 | `PROJECT_FILE_RELATIONSHIP_GUIDE.md` | 理解每个文件夹和关键代码文件的作用 |
| 3 | `PROJECT_FINAL_HANDOFF.md` | 理解项目完成到哪里、推荐 checkpoint 和最终结论 |
| 4 | `REPRODUCIBLE_EXPERIMENT_COMMANDS.md` | 学会如何跑测试、训练和 benchmark |
| 5 | `FINAL_DEFENSE_REPORT.md` | 如果要写结题报告或答辩，重点读这份 |

最小上手目标：

```powershell
conda activate torch_env
python -m pytest -q -p no:cacheprovider
```

看到测试通过后，再去跑 `REPRODUCIBLE_EXPERIMENT_COMMANDS.md` 里的 benchmark。

## 3. 文档分层

根目录文档可以分为六类。

### 3.1 第一入口

| 文档 | 作用 | 何时阅读 |
| --- | --- | --- |
| `README.md` | 文档总导航 | 第一个读 |
| `PROJECT_FILE_RELATIONSHIP_GUIDE.md` | 文件结构和模块关系说明 | 想知道文件之间怎么关联时 |
| `PROJECT_FINAL_HANDOFF.md` | 最终交接报告 | 想快速掌握项目状态和最终结论时 |
| `REPRODUCIBLE_EXPERIMENT_COMMANDS.md` | 可复现实验命令 | 准备运行代码或复现实验时 |

### 3.2 答辩与结题材料

| 文档/文件 | 作用 |
| --- | --- |
| `FINAL_DEFENSE_REPORT.md` | 论文式/结题式总报告 |
| `DEFENSE_PRESENTATION_OUTLINE.md` | 答辩 PPT 页面提纲和讲稿要点 |
| `UAV_MARL_MPC_DEFENSE_DECK.pptx` | 答辩 PPT 初版 |

这三份用于最终展示。正式答辩前建议人工打开 PPTX 检查排版，并补充成员、指导老师、学院、日期等信息。

### 3.3 核心算法报告

| 文档 | 作用 |
| --- | --- |
| `PATH_COST_REWARD_REPORT.md` | 说明 value loss 数值爆炸问题和 path-cost reward 修复 |
| `TRACKABILITY_REWARD_REPORT.md` | 说明 MAPPO 可跟踪性 reward，为什么 MPC 约束违反能降为 0 |
| `MAPPO_BENCHMARK_GUIDE.md` | 说明 MAPPO benchmark 的运行和对比方式 |
| `MULTISCENARIO_MAPPO_REPORT.md` | 说明多场景 MAPPO 实验 |
| `SCENARIO_REWARD_TUNING_REPORT.md` | 说明场景 reward 调参与实验观察 |

如果你要继续优化算法，优先读：

```text
PATH_COST_REWARD_REPORT.md
TRACKABILITY_REWARD_REPORT.md
MAPPO_BENCHMARK_GUIDE.md
```

### 3.4 实验结果报告

| 文档 | 作用 |
| --- | --- |
| `FINAL_EXPERIMENT_REPORT.md` | 阶段性实验总结 |
| `MULTISCENARIO_MAPPO_REPORT.md` | 多场景实验总结 |
| `TRACKABILITY_REWARD_REPORT.md` | 最新可跟踪性实验总结 |
| `FINAL_DEFENSE_REPORT.md` | 最终整合后的实验结论 |

最终引用实验结果时，以 `FINAL_DEFENSE_REPORT.md` 和 `PROJECT_FINAL_HANDOFF.md` 为准。

### 3.5 开发与运行手册

| 文档 | 作用 |
| --- | --- |
| `DEVELOPMENT_RUNBOOK.md` | 开发运行手册 |
| `REPRODUCIBLE_EXPERIMENT_COMMANDS.md` | 当前最完整的复现实验命令 |
| `README_WINDOWS.md` | 早期 Windows 数据包说明，主要用于理解原始交接数据 |

如果命令冲突，以 `REPRODUCIBLE_EXPERIMENT_COMMANDS.md` 为准。

### 3.6 历史任务说明

| 文档 | 作用 |
| --- | --- |
| `MARL_MPC_TASK_GUIDE.md` | 最初任务拆解与规划 |
| `README_WINDOWS.md` | 早期数据包说明 |

这两份适合了解项目来源，不建议作为当前执行入口。

## 4. 按角色阅读

### 4.1 如果你负责继续写代码

阅读顺序：

1. `PROJECT_FILE_RELATIONSHIP_GUIDE.md`
2. `PROJECT_FINAL_HANDOFF.md`
3. `REPRODUCIBLE_EXPERIMENT_COMMANDS.md`
4. `TRACKABILITY_REWARD_REPORT.md`

重点代码目录：

```text
src/planning/     路径生成算法
src/marl/         MAPPO 环境、reward、训练
src/mpc/          Robust MPC 跟踪
src/eval/         benchmark 和结果导出
```

### 4.2 如果你负责跑实验

阅读顺序：

1. `REPRODUCIBLE_EXPERIMENT_COMMANDS.md`
2. `PROJECT_FINAL_HANDOFF.md`
3. `TRACKABILITY_REWARD_REPORT.md`

重点配置：

```text
configs/default.yaml
configs/mappo_pathcost_long.yaml
configs/mappo_trackability_sweep.yaml
configs/mappo_trackability_multiseed.yaml
```

重点输出：

```text
outputs/mappo_pathcost_benchmark_final/
outputs/mappo_trackability_benchmark_final/
outputs/mappo_trackability_multiseed/
outputs/mappo_trackability_multiseed_best_benchmark/
```

### 4.3 如果你负责答辩和写报告

阅读顺序：

1. `FINAL_DEFENSE_REPORT.md`
2. `DEFENSE_PRESENTATION_OUTLINE.md`
3. `PROJECT_FINAL_HANDOFF.md`
4. `TRACKABILITY_REWARD_REPORT.md`

答辩材料：

```text
UAV_MARL_MPC_DEFENSE_DECK.pptx
FINAL_DEFENSE_REPORT.md
DEFENSE_PRESENTATION_OUTLINE.md
```

### 4.4 如果你负责数据和画像

阅读顺序：

1. `PROJECT_FILE_RELATIONSHIP_GUIDE.md`
2. `README_WINDOWS.md`
3. `data/uav_profiles/MAMBA_LITE_README.md`
4. `data/uav_profiles/TORCH_MAMBA_README.md`
5. `data/weather_cost_map/README.md`

重点关注：

```text
data/uav_profiles/
data/tasks/
data/weather_cost_map/
output_data/
```

## 5. 当前最重要的实验结论

### 5.1 path-cost MAPPO

推荐 checkpoint：

```text
outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt
```

作用：用于展示 MAPPO 在路径代价上优于 `marl_greedy`。

关键结果：

```text
completed_task_count = 5
total_path_cost = 6738.1788
mpc_constraint_violation_count = 21
```

### 5.2 trackability MAPPO

推荐 checkpoint：

```text
outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt
```

作用：用于展示 MAPPO 通过 reward 设计改善 MPC 可跟踪性。

关键结果：

```text
completed_task_count = 5
mpc_mean_tracking_error = 0.1204
mpc_constraint_violation_count = 0
```

### 5.3 多 seed 稳健性

推荐 checkpoint：

```text
outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt
```

关键结果：

```text
completed_task_count = 5
mpc_mean_tracking_error = 0.1533
mpc_constraint_violation_count = 0
```

## 6. 当前项目状态

当前代码、实验和文档状态：

```text
主干代码完成
核心优化完成
trackability sweep 完成
多 seed / 多 episode 实验完成
答辩报告和 PPT 初版完成
测试通过：37 passed
```

因此项目已经达到：

```text
可运行、可复现、可交接、可答辩
```

剩余工作主要是人工展示层面的内容：

1. 打开 `UAV_MARL_MPC_DEFENSE_DECK.pptx` 检查排版。
2. 补充答辩封面信息。
3. 根据老师要求决定是否替换正式 MAMBA 画像。
4. 如需论文级质量，可继续扩大训练 seed、episode 和任务规模。

## 7. 不建议新人一开始做的事

不要一上来就：

1. 重写路径规划算法。
2. 重新设计所有 reward。
3. 删除 outputs 目录。
4. 直接从旧的历史报告开始读。
5. 只看 PPT，不看 `PROJECT_FINAL_HANDOFF.md` 和 `REPRODUCIBLE_EXPERIMENT_COMMANDS.md`。

建议先跑通测试和最终 benchmark，再决定继续开发方向。

## 8. 快速命令

测试：

```powershell
python -m pytest -q -p no:cacheprovider
```

path-cost benchmark：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt --output-dir outputs/mappo_pathcost_benchmark_final
```

trackability benchmark：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt --output-dir outputs/mappo_trackability_benchmark_final
```

多 seed 实验：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_multiseed.yaml
```

## 9. 最后一句

如果你只记住一句话：

```text
先读 README.md，再读 PROJECT_FILE_RELATIONSHIP_GUIDE.md，
然后用 REPRODUCIBLE_EXPERIMENT_COMMANDS.md 跑通测试和 benchmark。
```
