# 可复现实验命令清单

本文档记录当前项目的推荐复现实验命令。默认工作目录为：

```powershell
E:\path_planning_handoff_windows
```

推荐使用 Conda 环境：

```powershell
conda activate torch_env
```

## 1. 环境检查

确认 Python 版本：

```powershell
python --version
```

推荐环境为 Python 3.10，例如：

```text
Python 3.10.20
```

运行单元测试：

```powershell
python -m pytest -q -p no:cacheprovider
```

说明：`-p no:cacheprovider` 用于避开 Windows 下 `.pytest_cache` 权限警告，不影响测试结果。

## 2. 基线与场景验证

运行多场景 baseline 验证：

```powershell
python examples/run_batch_experiments.py --suite configs/validation_scenarios.yaml
```

主要输出：

```text
outputs/validation_scenarios/batch_summary.csv
outputs/validation_scenarios/batch_summary.md
outputs/validation_scenarios/batch_metrics_long.csv
```

## 3. MAPPO path-cost 长训练

运行当前推荐的 path-cost reward 长训练：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_pathcost_long.yaml
```

主要输出：

```text
outputs/mappo_pathcost_long/mappo_experiment_summary.csv
outputs/mappo_pathcost_long/mappo_experiment_summary.md
outputs/mappo_pathcost_long/best_experiment.md
outputs/mappo_pathcost_long/pathcost_w50_e50/training_history.csv
outputs/mappo_pathcost_long/pathcost_w50_e50/policy_eval.csv
outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt
outputs/mappo_pathcost_long/pathcost_w50_e50/best_checkpoint.pt
```

当前推荐的默认场景演示 checkpoint：

```text
outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt
```

当前推荐的多场景验证 checkpoint：

```text
outputs/mappo_pathcost_long/pathcost_w50_e50/best_checkpoint.pt
```

## 4. 最终默认场景 benchmark

使用默认场景演示 checkpoint：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt --output-dir outputs/mappo_pathcost_benchmark_final
```

该命令现在默认会同时运行 Robust MPC 跟踪评估，因此比纯高层规划 benchmark 慢一些。

主要输出：

```text
outputs/mappo_pathcost_benchmark_final/comparison.md
outputs/mappo_pathcost_benchmark_final/metrics_with_mappo.csv
outputs/mappo_pathcost_benchmark_final/assignments_reference.csv
outputs/mappo_pathcost_benchmark_final/mappo_policy_eval.csv
outputs/mappo_pathcost_benchmark_final/mpc_tracking.csv
```

其中：

| 文件 | 作用 |
| --- | --- |
| `comparison.md` | baseline、MARL greedy、MAPPO 的统一指标对比表，包含 `mpc_*` 指标 |
| `metrics_with_mappo.csv` | CSV 版统一指标表 |
| `assignments_reference.csv` | 各方法的任务分配与路线摘要 |
| `mappo_policy_eval.csv` | MAPPO checkpoint 原始评估指标 |
| `mpc_tracking.csv` | 每条 route 的 MPC 跟踪误差、控制能耗、约束违反次数 |

如果只想快速比较高层规划，不运行 MPC，可以加：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt --output-dir outputs/mappo_pathcost_benchmark_final --skip-mpc
```

## 5. best checkpoint benchmark

使用多场景验证 best checkpoint：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_pathcost_long/pathcost_w50_e50/best_checkpoint.pt --output-dir outputs/mappo_pathcost_benchmark_best
```

主要输出：

```text
outputs/mappo_pathcost_benchmark_best/comparison.md
outputs/mappo_pathcost_benchmark_best/metrics_with_mappo.csv
outputs/mappo_pathcost_benchmark_best/assignments_reference.csv
outputs/mappo_pathcost_benchmark_best/mappo_policy_eval.csv
outputs/mappo_pathcost_benchmark_best/mpc_tracking.csv
```

## 6. MAPPO 可跟踪性优化实验

运行 trackability reward sweep：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_sweep.yaml
```

如果只想快速验证链路，可以先跑第一个实验：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_sweep.yaml --max-experiments 1
```

主要输出：

```text
outputs/mappo_trackability_sweep/mappo_experiment_summary.csv
outputs/mappo_trackability_sweep/mappo_experiment_summary.md
outputs/mappo_trackability_sweep/best_experiment.md
outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt
```

使用当前 smoke run checkpoint 做 MPC benchmark：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt --output-dir outputs/mappo_trackability_benchmark_smoke
```

主要输出：

```text
outputs/mappo_trackability_benchmark_smoke/comparison.md
outputs/mappo_trackability_benchmark_smoke/mpc_tracking.csv
```

该结果用于展示“路径可跟踪性优化”：MPC 约束违反次数可以从旧 MAPPO 的 21 降到 0，但路径总代价会上升。

完整多 seed / 多 episode 稳健性实验：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_trackability_multiseed.yaml
```

主要输出：

```text
outputs/mappo_trackability_multiseed/mappo_experiment_summary.md
outputs/mappo_trackability_multiseed/best_experiment.md
outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt
```

benchmark 多 seed 最优 checkpoint：

```powershell
python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt --output-dir outputs/mappo_trackability_multiseed_best_benchmark
```

## 7. 单独运行 Robust MPC 跟踪验证

使用 MARL greedy 高层路径做 MPC 跟踪验证：

```powershell
python examples/run_mpc_from_scenario.py --method marl_greedy
```

也可以替换为：

```powershell
python examples/run_mpc_from_scenario.py --method weather_grid
python examples/run_mpc_from_scenario.py --method sequential
```

该脚本用于单独观察某一种方法的一条 route 如何被 MPC 跟踪。正式汇总结果应优先查看最终 benchmark 的：

```text
outputs/mappo_pathcost_benchmark_final/mpc_tracking.csv
```

## 8. 三维气象路径验证

运行三维气象路径规划示例：

```powershell
python examples/run_weather_3d_path.py
```

该命令用于确认 weather-3D 路径动作与气象代价计算是否正常。

## 9. 可选长实验

如果有更多训练时间，可以运行历史长训练套件：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_long_experiments.yaml
```

也可以运行多场景 MAPPO 套件：

```powershell
python examples/run_mappo_experiments.py --suite configs/mappo_multiscenario_experiments.yaml
```

对应输出：

```text
outputs/mappo_long_experiments/
outputs/mappo_multiscenario_experiments/
```

## 10. 建议复现实验顺序

从零复现时，推荐顺序如下：

1. `python -m pytest -q -p no:cacheprovider`
2. `python examples/run_batch_experiments.py --suite configs/validation_scenarios.yaml`
3. `python examples/run_mappo_experiments.py --suite configs/mappo_pathcost_long.yaml`
4. `python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_pathcost_long/pathcost_w50_e50/mappo_checkpoint.pt --output-dir outputs/mappo_pathcost_benchmark_final`
5. `python examples/run_mappo_experiments.py --suite configs/mappo_trackability_sweep.yaml --max-experiments 1`
6. `python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_sweep/pathcost_w50_track_w25_e30/best_checkpoint.pt --output-dir outputs/mappo_trackability_benchmark_smoke`
7. `python examples/run_mappo_experiments.py --suite configs/mappo_trackability_multiseed.yaml`
8. `python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt --output-dir outputs/mappo_trackability_multiseed_best_benchmark`
9. 查看 `outputs/mappo_pathcost_benchmark_final/comparison.md`
10. 查看 `outputs/mappo_trackability_benchmark_final/comparison.md`
11. 查看 `FINAL_DEFENSE_REPORT.md` 和 `UAV_MARL_MPC_DEFENSE_DECK.pptx`

## 11. 当前结果口径

当前默认场景最终结果以以下文件为准：

```text
outputs/mappo_pathcost_benchmark_final/comparison.md
```

当前 MPC 逐路线跟踪结果以以下文件为准：

```text
outputs/mappo_pathcost_benchmark_final/mpc_tracking.csv
```

当前 MAPPO 可跟踪性优化结果以以下文件为准：

```text
outputs/mappo_trackability_benchmark_smoke/comparison.md
outputs/mappo_trackability_benchmark_smoke/mpc_tracking.csv
TRACKABILITY_REWARD_REPORT.md
```

当前多场景 checkpoint 选择结果以以下文件为准：

```text
outputs/mappo_pathcost_long/best_experiment.md
```

当前项目最终交接说明以以下文件为准：

```text
PROJECT_FINAL_HANDOFF.md
```

当前答辩/结题材料：

```text
FINAL_DEFENSE_REPORT.md
DEFENSE_PRESENTATION_OUTLINE.md
UAV_MARL_MPC_DEFENSE_DECK.pptx
```
