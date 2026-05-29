# 项目文件关系与作用说明

本文档用于帮助后续参与人员快速理解本项目的文件结构、模块关系和使用方式。建议新成员先阅读 `README.md`，再阅读本文档、`PROJECT_FINAL_HANDOFF.md` 和 `REPRODUCIBLE_EXPERIMENT_COMMANDS.md`。

## 1. 项目整体关系

本项目的核心目标是：结合无人机个体画像、任务需求和三维气象地图，使用 MARL/MAPPO 完成任务分配与路径规划，并结合 Robust MPC 完成底层航迹跟踪。

整体文件关系可以理解为：

```mermaid
flowchart LR
    A["data 原始/处理后数据"] --> B["configs 实验配置"]
    B --> C["src/data_io 场景读取"]
    C --> D["src/core 基础计算"]
    D --> E["src/baseline / src/planning / src/marl 高层规划"]
    E --> F["src/mpc 底层轨迹跟踪"]
    E --> G["src/eval 评估导出"]
    F --> G
    G --> H["outputs 实验结果"]
    H --> I["根目录 Markdown 报告"]
```

简单来说：

1. `data/` 提供输入数据。
2. `configs/` 决定实验如何运行。
3. `src/` 存放核心代码。
4. `examples/` 是可直接运行的脚本入口。
5. `outputs/` 保存实验结果。
6. `tests/` 用于验证代码是否正常。
7. 根目录 Markdown 文档用于交接、说明和复现。

## 2. 根目录文档

根目录下的 Markdown 文档主要是给项目成员、老师或后续开发者看的说明材料。

| 文件 | 作用 |
| --- | --- |
| `PROJECT_FINAL_HANDOFF.md` | 最终交接总入口，说明项目完成状态、推荐 checkpoint、实验结论和后续任务 |
| `REPRODUCIBLE_EXPERIMENT_COMMANDS.md` | 可复现实验命令清单，说明如何重新跑测试、训练和 benchmark |
| `PROJECT_FILE_RELATIONSHIP_GUIDE.md` | 本文档，说明各个文件夹和关键文件之间的关系 |
| `FINAL_DEFENSE_REPORT.md` | 最终结题/论文式报告 |
| `DEFENSE_PRESENTATION_OUTLINE.md` | 答辩 PPT 页面提纲与讲稿要点 |
| `MARL_MPC_TASK_GUIDE.md` | 项目任务指南，说明最初的任务拆解和技术路线 |
| `DEVELOPMENT_RUNBOOK.md` | 开发运行手册，帮助成员了解常用运行方式 |
| `MAPPO_BENCHMARK_GUIDE.md` | MAPPO benchmark 说明 |
| `FINAL_EXPERIMENT_REPORT.md` | 阶段性最终实验报告 |
| `PATH_COST_REWARD_REPORT.md` | path-cost reward 与 value loss 数值问题修复报告 |
| `TRACKABILITY_REWARD_REPORT.md` | MAPPO 可跟踪性 reward 优化报告 |
| `MULTISCENARIO_MAPPO_REPORT.md` | 多场景 MAPPO 实验报告 |
| `SCENARIO_REWARD_TUNING_REPORT.md` | 场景 reward 调参与实验说明 |

建议阅读顺序：

1. `README.md`
2. `PROJECT_FILE_RELATIONSHIP_GUIDE.md`
3. `PROJECT_FINAL_HANDOFF.md`
4. `REPRODUCIBLE_EXPERIMENT_COMMANDS.md`
5. 其他专题报告

## 3. `data/` 数据目录

`data/` 是项目的输入数据目录，算法运行时会从这里读取无人机画像、任务点和气象代价地图。

### 3.1 `data/uav_profiles/`

该目录保存无人机个体画像数据。

常见文件：

| 文件 | 作用 |
| --- | --- |
| `uav_profiles.csv` | 基础 UAV 能力画像数据 |
| `mamba_uav_dynamic_profiles.csv` | MAMBA-Lite 生成或整理出的动态画像 |
| `mamba_lite_metrics.json` | MAMBA-Lite 画像相关指标 |
| `MAMBA_LITE_README.md` | 说明当前 MAMBA-Lite 版本不是正式 MAMBA，后续可继续优化 |
| `torch_mamba_uav_dynamic_profiles.csv` | Torch MAMBA 版本生成的 UAV 动态画像 |
| `torch_mamba_uav_profile_model.pt` | Torch MAMBA 模型权重 |
| `TORCH_MAMBA_README.md` | Torch MAMBA 版本说明 |

当前项目已经把 MAMBA-Lite 画像作为无人机能力输入使用。后续如果要增强成果，可以把这里替换为更正式的 MAMBA 模型输出。

### 3.2 `data/tasks/`

该目录保存任务数据。

关键文件：

| 文件 | 作用 |
| --- | --- |
| `demo_tasks.csv` | 默认任务点数据，包括任务位置、任务需求等 |

任务数据会被 `src/data_io/task_loader.py` 读取，并进入 MARL 环境和 baseline 算法。

### 3.3 `data/weather_cost_map/`

该目录保存处理后的气象代价地图。

常见文件：

| 文件 | 作用 |
| --- | --- |
| `weather_cost_map_prototype.csv` | 原型气象代价地图 |
| `weather_cost_map_sample_24h.csv` | 24 小时样例气象代价地图 |
| `README.md` | 气象地图数据说明 |

气象地图用于路径规划中的风险和代价计算，也会影响 MARL reward。

## 4. `output_data/` 原始气象数据

`output_data/` 中保存不同地区、不同时间段的气象 CSV 数据，例如：

```text
安徽合肥巢湖_2026-03-15_2026-04-30.csv
四川盆地_2025-12-15_2026-02-01.csv
云南大理苍山_2025-10-01_2025-11-01.csv
西藏拉萨_2025-06-15_2025-08-01.csv
海南万宁_2026-03-15_2026-04-30.csv
新疆_2025-10-01_2025-11-01.csv
```

这些数据更接近原始气象数据，可以用于生成 `data/weather_cost_map/` 下的气象代价地图。

## 5. `configs/` 配置目录

`configs/` 决定实验如何运行，包括数据路径、算法参数、reward 权重、训练 episode、输出目录等。

| 文件 | 作用 |
| --- | --- |
| `default.yaml` | 默认主配置，最重要，很多脚本默认读取它 |
| `experiments.yaml` | baseline 批量实验配置 |
| `validation_scenarios.yaml` | 多场景验证配置 |
| `mappo_experiments.yaml` | 短 MAPPO 训练实验配置 |
| `mappo_long_experiments.yaml` | 长 MAPPO 训练实验配置 |
| `mappo_reward_sweep.yaml` | reward 权重搜索实验配置 |
| `mappo_pathcost_sweep.yaml` | path-cost reward 小规模搜索配置 |
| `mappo_pathcost_long.yaml` | 当前推荐的 path-cost reward 长训练配置 |
| `mappo_trackability_sweep.yaml` | MAPPO 可跟踪性 reward 优化配置，用于减少长 direct 航段 |
| `mappo_trackability_multiseed.yaml` | MAPPO 可跟踪性多 seed / 多 episode 稳健性配置 |
| `mappo_validation_same_action.yaml` | MAPPO 同动作空间验证配置 |
| `mappo_multiscenario_experiments.yaml` | 多场景 MAPPO 训练配置 |

配置文件的作用可以概括为：

```text
configs 决定用什么数据、跑什么算法、reward 怎么算、训练多久、结果存到哪里。
```

## 6. `src/` 核心代码目录

`src/` 是项目真正的程序主体。

### 6.1 `src/core/`

基础计算层，其他模块都会依赖它。

| 文件 | 作用 |
| --- | --- |
| `schemas.py` | 定义 UAV、Task、WeatherCell 等核心数据结构 |
| `geo_utils.py` | 计算地理距离、坐标相关工具 |
| `cost_model.py` | 计算路径代价、气象代价、能耗代价等 |

可以理解为：`src/core/` 提供所有算法共同使用的“数学和数据结构基础”。

### 6.2 `src/data_io/`

数据读取层，把 CSV、JSON、YAML 等文件转换成程序可以使用的对象。

| 文件 | 作用 |
| --- | --- |
| `profile_loader.py` | 读取无人机画像数据 |
| `task_loader.py` | 读取任务数据 |
| `weather_loader.py` | 读取气象代价地图 |
| `scenario_loader.py` | 读取配置并组装完整实验场景 |

关键关系：

```text
data/uav_profiles + data/tasks + data/weather_cost_map + configs/default.yaml
    -> src/data_io/scenario_loader.py
    -> 可运行场景对象
```

### 6.3 `src/baseline/`

baseline 算法目录，用于和 MARL/MAPPO 进行对比。

| 文件 | 作用 |
| --- | --- |
| `rule_assignment.py` | 规则分配算法 |
| `sequential_assignment.py` | 顺序任务分配算法 |
| `shortest_path.py` | 最短路径相关 baseline |
| `weather_aware_assignment.py` | 气象感知任务分配 baseline |

这些算法一般不需要训练，主要用于形成对照组。

### 6.4 `src/planning/`

路径规划层，负责根据气象地图和任务点生成路径。

| 文件 | 作用 |
| --- | --- |
| `weather_grid_path.py` | 二维气象网格路径规划 |
| `weather_3d_path.py` | 三维气象路径规划 |

其中 `weather_grid_path.py` 当前是非常强的 baseline，在默认场景中路径代价优于当前 MAPPO。

### 6.5 `src/marl/`

MARL/MAPPO 核心目录，是本项目最重要的算法模块。

| 文件 | 作用 |
| --- | --- |
| `action_space.py` | 定义智能体可选动作，例如任务选择、等待、气象路径动作等 |
| `env.py` | 基础 MARL 环境 |
| `scenario_env.py` | 基于真实场景数据构建 MARL 环境 |
| `reward.py` | reward 计算，包括任务完成、距离、气象、能耗、path-cost 惩罚 |
| `policy.py` | 策略网络相关代码 |
| `train_mappo.py` | MAPPO 训练、评估、checkpoint 保存核心逻辑 |

关键训练链路：

```text
configs/mappo_pathcost_long.yaml
    -> src/data_io/scenario_loader.py
    -> src/marl/scenario_env.py
    -> src/marl/train_mappo.py
    -> outputs/mappo_pathcost_long/
```

### 6.6 `src/mpc/`

底层控制与航迹跟踪目录。

| 文件 | 作用 |
| --- | --- |
| `dynamics.py` | 无人机运动学/动力学模型 |
| `wind_model.py` | 风场扰动模型 |
| `robust_mpc.py` | Robust MPC / QP 控制核心 |
| `route_tracking.py` | 将高层路径转换为可跟踪轨迹 |

它的作用是把高层任务路径进一步变成可执行的控制轨迹，用于体现“规划 + 管控”的闭环。

### 6.7 `src/eval/`

评估与结果导出目录。

| 文件 | 作用 |
| --- | --- |
| `metrics.py` | 计算实验指标 |
| `export.py` | 导出结果文件 |
| `report.py` | 生成 Markdown/CSV 报告 |
| `scenario_eval.py` | 场景评估 |
| `training_export.py` | 导出训练历史和训练曲线 |
| `mappo_checkpoint.py` | 加载并评估 MAPPO checkpoint |
| `mpc_eval.py` | 批量评估各方法 route 的 Robust MPC 跟踪误差、控制能耗和约束违反次数 |
| `compare_baseline_marl.py` | 比较 baseline 与 MARL/MAPPO |

常见输出包括 `comparison.md`、`comparison.csv`、`training_history.csv`、`policy_eval.csv`。

### 6.8 `src/viz/`

可视化目录。

| 文件 | 作用 |
| --- | --- |
| `plot_weather_map.py` | 绘制气象地图 |
| `plot_routes.py` | 绘制路径和任务分配结果 |

主要用于生成 `outputs/` 中的图片，例如路径图和气象图。

## 7. `examples/` 脚本入口目录

`examples/` 是平时最常运行的目录。一般不直接运行 `src/` 里的模块，而是运行 `examples/` 中的脚本。

| 文件 | 作用 |
| --- | --- |
| `read_handoff_data.py` | 读取并检查交接数据 |
| `demo_setup.py` | 演示项目基础设置 |
| `run_baseline.py` | 运行基础 baseline |
| `run_scenario.py` | 运行一个完整场景 |
| `run_batch_experiments.py` | 批量运行 baseline/场景实验 |
| `summarize_batch_results.py` | 汇总批量实验结果 |
| `run_weather_grid_path.py` | 运行二维气象网格路径规划 |
| `run_weather_3d_path.py` | 运行三维气象路径规划 |
| `run_sequential_baseline.py` | 运行 sequential baseline |
| `run_marl_eval.py` | 运行 MARL 评估 |
| `run_mappo_train.py` | 单次 MAPPO 训练 |
| `run_mappo_experiments.py` | 批量 MAPPO 实验 |
| `run_mappo_benchmark.py` | MAPPO 与 baseline 对比 benchmark |
| `evaluate_mappo_policy.py` | 单独评估 MAPPO 策略 |
| `run_mpc_tracking.py` | MPC 路径跟踪示例 |
| `run_qp_mpc_tracking.py` | QP-MPC 路径跟踪示例 |
| `run_mpc_from_scenario.py` | 从场景规划结果接入 MPC 跟踪 |

可以理解为：

```text
examples/ 是按钮
src/ 是机器内部
data/ 是输入
outputs/ 是结果
```

## 8. `outputs/` 实验输出目录

`outputs/` 保存所有实验运行后的结果。它不是核心源码，但对写报告和复现实验非常重要。

重要目录：

| 目录 | 作用 |
| --- | --- |
| `outputs/default_scenario/` | 默认场景 baseline 输出 |
| `outputs/validation_scenarios/` | 多场景验证输出 |
| `outputs/mappo_train/` | 单次 MAPPO 训练输出 |
| `outputs/mappo_experiments/` | 短 MAPPO 实验输出 |
| `outputs/mappo_long_experiments/` | 历史长 MAPPO 实验输出 |
| `outputs/mappo_reward_sweep/` | reward 权重搜索输出 |
| `outputs/mappo_pathcost_sweep/` | path-cost reward 小规模搜索输出 |
| `outputs/mappo_pathcost_long/` | 当前推荐 path-cost 长训练输出 |
| `outputs/mappo_pathcost_benchmark_final/` | 当前最终默认场景 benchmark 输出 |
| `outputs/mappo_pathcost_benchmark_best/` | best checkpoint benchmark 输出 |
| `outputs/mappo_trackability_sweep/` | MAPPO 可跟踪性 reward 训练输出 |
| `outputs/mappo_trackability_benchmark_smoke/` | 可跟踪性 checkpoint 的 MPC benchmark 输出 |
| `outputs/mappo_trackability_benchmark_final/` | 完整 trackability sweep 最优 checkpoint benchmark 输出 |
| `outputs/mappo_trackability_multiseed/` | 多 seed / 多 episode 稳健性训练输出 |
| `outputs/mappo_trackability_multiseed_best_benchmark/` | 多 seed 最优 checkpoint benchmark 输出 |
| `outputs/mappo_multiscenario_experiments/` | 多场景 MAPPO 训练输出 |

常见输出文件：

| 文件名 | 作用 |
| --- | --- |
| `training_history.csv` | 每个 episode 的训练过程 |
| `training_summary.csv` | 训练汇总指标 |
| `training_summary.md` | 训练汇总报告 |
| `training_curves.png` | 训练曲线图 |
| `policy_eval.csv` | 策略评估结果 |
| `checkpoint_eval_history.csv` | checkpoint 评估历史 |
| `best_policy_eval.csv` | best checkpoint 的策略评估 |
| `mappo_checkpoint.pt` | 最终训练 checkpoint |
| `best_checkpoint.pt` | 验证集最优 checkpoint |
| `comparison.csv` | 算法对比表 |
| `comparison.md` | Markdown 版算法对比表 |
| `mpc_tracking.csv` | 每条 route 的 MPC 跟踪结果，包括误差、控制能耗和约束违反次数 |
| `metrics.csv` | 场景指标结果 |
| `assignments.csv` | 任务分配结果 |

当前最值得关注的输出是：

```text
outputs/mappo_pathcost_long/
outputs/mappo_pathcost_benchmark_final/
outputs/validation_scenarios/
```

## 9. `tests/` 测试目录

`tests/` 用于确认各模块是否正常工作。每次改代码后建议运行：

```powershell
python -m pytest -q -p no:cacheprovider
```

常见测试文件：

| 文件 | 作用 |
| --- | --- |
| `test_geo_utils.py` | 测试地理距离计算 |
| `test_cost_model.py` | 测试代价模型 |
| `test_task_loader.py` | 测试任务读取 |
| `test_weather_grid_path.py` | 测试二维气象路径 |
| `test_weather_3d_path.py` | 测试三维气象路径 |
| `test_marl_grid_reward.py` | 测试 MARL 网格 reward |
| `test_marl_3d_reward.py` | 测试三维气象 reward |
| `test_reward_config.py` | 测试 reward 权重与 path-cost reward 是否生效 |
| `test_mappo_action_mask.py` | 测试 MAPPO 动作掩码 |
| `test_mappo_checkpoint_eval.py` | 测试 MAPPO checkpoint 评估 |
| `test_mappo_experiments.py` | 测试 MAPPO 实验配置 |
| `test_mpc.py` | 测试 MPC 基础功能 |
| `test_qp_mpc.py` | 测试 QP-MPC |
| `test_mpc_eval.py` | 测试 MPC 指标能否并入真实 assignment 结果 |
| `test_report.py` | 测试报告导出 |

如果测试全部通过，说明当前主要功能链路没有断。

## 10. 构建脚本

根目录下还有一些构建数据的脚本：

| 文件 | 作用 |
| --- | --- |
| `build_weather_cost_map.py` | 从原始气象数据构建气象代价地图 |
| `build_uav_profiles.py` | 构建基础 UAV profiles |
| `build_mamba_uav_profiles.py` | 构建 MAMBA-Lite UAV profiles |
| `build_torch_mamba_uav_profiles.py` | 构建 Torch MAMBA UAV profiles |

这些脚本主要用于准备 `data/` 目录下的数据。

## 11. 核心运行链路示例

### 11.1 跑默认 benchmark

```text
configs/default.yaml
    -> examples/run_mappo_benchmark.py
    -> src/data_io/scenario_loader.py
    -> src/baseline/ + src/planning/ + src/marl/
    -> src/eval/mpc_eval.py
    -> src/eval/
    -> outputs/mappo_pathcost_benchmark_final/
```

### 11.2 跑 MAPPO 训练

```text
configs/mappo_pathcost_long.yaml
    -> examples/run_mappo_experiments.py
    -> src/marl/train_mappo.py
    -> src/marl/scenario_env.py
    -> src/marl/reward.py
    -> outputs/mappo_pathcost_long/
```

### 11.3 跑多场景验证

```text
configs/validation_scenarios.yaml
    -> examples/run_batch_experiments.py
    -> src/data_io/scenario_loader.py
    -> src/baseline/ + src/planning/
    -> src/eval/
    -> outputs/validation_scenarios/
```

### 11.4 跑 MPC 跟踪

```text
examples/run_mpc_from_scenario.py
    -> src/data_io/scenario_loader.py
    -> 高层路径规划结果
    -> src/mpc/route_tracking.py
    -> src/mpc/robust_mpc.py
    -> MPC 跟踪指标
```

## 12. 新成员建议学习路线

如果是第一次接触本项目，建议按下面顺序学习：

1. 阅读 `PROJECT_FILE_RELATIONSHIP_GUIDE.md`，理解文件结构。
2. 阅读 `PROJECT_FINAL_HANDOFF.md`，理解项目当前完成度。
3. 阅读 `REPRODUCIBLE_EXPERIMENT_COMMANDS.md`，掌握如何复现实验。
4. 查看 `configs/default.yaml`，理解默认场景配置。
5. 查看 `src/data_io/scenario_loader.py`，理解数据如何进入程序。
6. 查看 `src/core/cost_model.py`，理解代价如何计算。
7. 查看 `src/marl/reward.py`，理解 MARL reward 如何设计。
8. 查看 `src/marl/train_mappo.py`，理解 MAPPO 如何训练。
9. 查看 `examples/run_mappo_benchmark.py`，理解算法如何对比。
10. 查看 `outputs/mappo_pathcost_benchmark_final/comparison.md`，理解当前实验结果。

## 13. 一句话总结

本项目的文件关系可以概括为：

```text
data 提供输入
configs 决定实验参数
src/data_io 读取场景
src/core 提供基础计算
src/baseline、src/planning、src/marl 完成任务分配和路径规划
src/mpc 完成底层航迹跟踪
src/eval 和 src/viz 输出指标和图片
outputs 保存实验结果
根目录 Markdown 文档解释项目状态和复现方式
```

也可以进一步简化为：

```text
输入数据 -> 配置文件 -> 核心算法 -> 实验脚本 -> 输出结果 -> 报告文档
```
