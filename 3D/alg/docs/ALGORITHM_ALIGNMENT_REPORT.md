# 项目书算法对齐报告

本文档说明当前工程如何从原型版对齐到项目书中的：

```text
GPR 三维动态气象建模
+ Mamba 异构无人机个体画像
+ MARL 协同任务分配
+ Robust MPC 抗扰动航轨跟踪
```

## 1. 当前最终算法链路

```text
GPR weather cost map
  -> Mamba UAV dynamic profiles
  -> MAPPO as MARL implementation
  -> weather_grid / weather_3D route generation
  -> Robust MPC tracking evaluation
```

其中：

- `MAPPO` 是 `MARL` 的具体实现。
- `weather_3D` 是高层策略可选择的气象约束路径生成方式。
- `Robust MPC` 用于验证高层航迹是否能够被底层控制器稳定跟踪。

## 2. 已完成改造

| 项目书模块 | 当前实现 | 关键文件 |
| --- | --- | --- |
| GPR 三维动态气象建模 | 已新增 GPR 版本气象代价地图 | `build_gpr_weather_cost_map.py` |
| Mamba 个体画像 | 已整理为 Mamba 正式接口，支持官方后端可选回退 | `build_torch_mamba_uav_profiles.py` |
| MARL 协同任务分配 | 使用 MAPPO 作为 MARL 具体实现 | `src/marl/` |
| Robust MPC 抗扰动跟踪 | 已接入 benchmark 并输出 MPC 指标 | `src/mpc/`, `src/eval/mpc_eval.py` |
| Web/QT 可视化对接 | 已新增完整 waypoint CSV 导出 | `src/eval/export.py` |

## 3. 新增/更新数据

GPR 气象地图：

```text
data/weather_cost_map/weather_cost_map_gpr_sample_24h.csv
data/weather_cost_map/weather_cost_map_gpr.csv
data/weather_cost_map/gpr_weather_metrics.json
```

Mamba 动态画像：

```text
data/uav_profiles/mamba_uav_dynamic_profiles_official.csv
data/uav_profiles/torch_mamba_uav_dynamic_profiles.csv
data/uav_profiles/torch_mamba_metrics.json
```

当前 `configs/default.yaml` 已切换为：

```yaml
paths:
  weather_map: data/weather_cost_map/weather_cost_map_gpr_sample_24h.csv
  dynamic_profiles: data/uav_profiles/mamba_uav_dynamic_profiles_official.csv
```

## 4. GPR 建模说明

新增脚本：

```text
build_gpr_weather_cost_map.py
```

它使用：

```text
sklearn.gaussian_process.GaussianProcessRegressor
ConstantKernel * RBF + WhiteKernel
```

对每个时间片、每个高度层进行稀疏观测 GPR 建模，并保持原有 weather map CSV 字段不变。

当前数据只有 6 个代表性地区观测点，因此该 GPR 属于稀疏观测原型。后续如接入 ERA5 或 Open-Meteo 多网格点数据，脚本结构可以继续复用。

## 5. Mamba 画像说明

新增正式接口输出：

```text
data/uav_profiles/mamba_uav_dynamic_profiles_official.csv
```

脚本 `build_torch_mamba_uav_profiles.py` 会优先尝试：

```text
mamba_ssm.Mamba
```

如果环境没有官方 `mamba-ssm`，则自动回退到当前 PyTorch 选择性状态空间块：

```text
SelectiveStateSpaceBlock
```

这样做的好处是：

- 输出字段对路径规划完全兼容。
- Windows/macOS 不安装官方 Mamba 也能稳定复现。
- 后续安装 `mamba-ssm` 后可无缝切换到官方 Mamba block。

## 6. 重新运行结果

已运行：

```bash
conda run -n py311 python examples/run_weather_3d_path.py
conda run -n py311 python examples/run_mappo_benchmark.py --config configs/default.yaml --checkpoint outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt --output-dir outputs/gpr_mamba_mappo_benchmark
```

输出目录：

```text
outputs/gpr_mamba_mappo_benchmark/
```

关键输出：

```text
comparison.md
metrics_with_mappo.csv
assignments_reference.csv
planned_routes_waypoints.csv
mappo_policy_eval.csv
mpc_tracking.csv
```

当前 GPR + Mamba + MAPPO benchmark 中：

- MAPPO 完成全部 5 个任务。
- MAPPO 使用了 `3` 条 weather-3D 路径和 `2` 条 weather-grid 路径。
- MAPPO 的 MPC 约束违反次数为 `0`。
- 已生成完整航迹点文件 `planned_routes_waypoints.csv`，可直接供 Qt 3D 可视化读取。

## 7. Qt 3D 可视化接口

新增输出：

```text
outputs/gpr_mamba_mappo_benchmark/planned_routes_waypoints.csv
```

字段：

```text
method,uav_id,task_id,leg_index,route_strategy,point_index,latitude,longitude,height_m,weather_cost
```

可视化建议：

- 按 `method == mappo_checkpoint` 过滤最终 MAPPO 路径。
- 按 `uav_id + task_id + leg_index` 分组绘制航迹线。
- 用 `height_m` 作为 Z 轴。
- 用 `weather_cost` 映射颜色。

## 8. 最终对外表述

建议统一写成：

```text
本项目基于 GPR 构建三维动态气象代价地图，基于 Mamba 风格状态空间模型构建无人机动态个体画像，并采用 MAPPO 作为 MARL 的具体实现完成多无人机任务分配与路径策略选择，最后通过 Robust MPC 对生成航迹进行底层抗扰动跟踪验证。
```

## 9. 仍需说明的边界

- 当前 GPR 使用 6 个地区代表点，属于稀疏观测原型。
- 当前环境未安装官方 `mamba-ssm`，所以本次运行使用 `selective_ssm` 回退后端，但接口已支持官方 Mamba。
- MAPPO 不需要替换，它是 MARL 的一种具体实现。

