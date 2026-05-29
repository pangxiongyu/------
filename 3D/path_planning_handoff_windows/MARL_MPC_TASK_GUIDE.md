# MARL 与 Robust MPC 联合规划任务清单

本文档用于指导后续程序编写。当前项目已有三维气象代价地图、统计版无人机画像、Mamba-lite / PyTorch Mamba 风格动态画像。后续开发重点是基于这些结果构建多无人机联合任务分配、路径规划与底层轨迹管控平台。

## 0. 项目目标

构建一个联合规划与管控框架：

```text
三维气象地图 + 无人机个体画像
        -> MARL 全局任务分配与路径匹配
        -> Robust MPC 局部航迹跟踪与抗扰动控制
        -> 评估与可视化
```

核心目标：

- 利用气象代价 `weather_cost` 规避高风险区域。
- 利用无人机动态画像匹配合适任务。
- 利用 MARL 完成多无人机、多任务的联合优化。
- 利用 Robust MPC 抵抗风扰并跟踪 MARL 输出的参考航迹。
- 对比规则 baseline，证明 MARL 和 MPC 的改进效果。

## 1. 当前已有文件与可用数据

### 1.1 气象地图

目录：

```text
data/weather_cost_map/
```

优先读取：

```text
data/weather_cost_map/weather_cost_map_sample_24h.csv
```

跑通后切换到：

```text
data/weather_cost_map/weather_cost_map_prototype.csv
```

关键字段：

```text
time
latitude
longitude
height_m
cost
wind_speed
wind_direction
temperature_2m
relative_humidity_2m
weather_code
```

程序侧重点：

- `cost` 是路径规划最重要字段，范围约为 `0-1`。
- `height_m` 当前主要为 `10m` 和 `100m`。
- `wind_speed` 和 `wind_direction` 后续用于 Robust MPC 风扰输入。

### 1.2 无人机画像

目录：

```text
data/uav_profiles/
```

优先读取：

```text
data/uav_profiles/torch_mamba_uav_dynamic_profiles.csv
```

可作为补充或对比：

```text
data/uav_profiles/uav_profiles.csv
data/uav_profiles/mamba_uav_dynamic_profiles.csv
```

动态画像关键字段：

```text
flight_id
route
payload_g
target_altitude_m
window_start_s
window_end_s
pred_voltage_drop_v
pred_avg_current_a
pred_stability_risk
pred_stability_pressure
dynamic_health_score
dynamic_risk_level
```

注意：

- `Mamba-lite` 不是正式官方 Mamba，只是先跑通链路的轻量版本。
- `torch_mamba_uav_dynamic_profiles.csv` 是当前路径规划优先使用的画像结果。
- 后续可以把画像模型升级为官方 `mamba-ssm`，但不应阻塞第一阶段 MARL 开发。

## 2. 推荐代码目录结构

后续建议新增如下目录：

```text
src/
  data_io/
    weather_loader.py
    profile_loader.py
    task_loader.py
  core/
    schemas.py
    cost_model.py
    geo_utils.py
  baseline/
    rule_assignment.py
    shortest_path.py
  marl/
    env.py
    reward.py
    train_mappo.py
    policy.py
  mpc/
    dynamics.py
    robust_mpc.py
    wind_model.py
  eval/
    metrics.py
    compare_baseline_marl.py
  viz/
    plot_weather_map.py
    plot_routes.py
examples/
  run_baseline.py
  run_marl_eval.py
  run_mpc_tracking.py
```

第一阶段不必一次性全部实现，建议按本文档顺序逐步创建。

## 3. 阶段一：数据读取与统一接口

### 3.1 气象地图读取模块

建议文件：

```text
src/data_io/weather_loader.py
```

任务：

- 读取 `weather_cost_map_sample_24h.csv`。
- 支持读取完整版 `weather_cost_map_prototype.csv`。
- 提供按时间、高度、经纬度查询最近网格点的函数。
- 提供按时间和高度提取二维气象层的函数。
- 返回标准字段：`weather_cost`, `wind_speed`, `wind_direction`, `height_m`。

建议接口：

```python
load_weather_map(path) -> WeatherMap
query_weather(time, lat, lon, height_m) -> WeatherCell
get_weather_layer(time, height_m) -> DataFrame
```

验收标准：

- 能读取样本 24 小时气象地图。
- 能查询任意候选点附近的 `cost`。
- 能输出一个固定时间和高度层的气象代价矩阵或表格。

### 3.2 无人机画像读取模块

建议文件：

```text
src/data_io/profile_loader.py
```

任务：

- 读取 `torch_mamba_uav_dynamic_profiles.csv`。
- 支持按 `flight_id` 查询画像。
- 支持过滤 `dynamic_risk_level != high` 的可用无人机窗口。
- 支持选择每架无人机最新或最优画像窗口。

建议接口：

```python
load_dynamic_profiles(path) -> DataFrame
select_available_profiles(max_risk="medium") -> DataFrame
get_profile_features(flight_id, window_id=None) -> UavProfile
```

验收标准：

- 能输出每架无人机的 `dynamic_health_score`。
- 能识别 `low / medium / high` 风险等级。
- 能为 MARL 环境提供固定维度画像特征。

### 3.3 任务与无人机状态结构

建议文件：

```text
src/core/schemas.py
```

需要定义：

```text
UavState
TaskState
WeatherCell
UavProfile
RoutePlan
AssignmentResult
```

建议字段：

```text
UavState:
  uav_id
  current_lat
  current_lon
  current_height_m
  payload_capacity_g
  profile_features
  assigned_task_id
  status

TaskState:
  task_id
  target_lat
  target_lon
  target_height_m
  payload_g
  deadline
  priority
  status
```

验收标准：

- baseline、MARL、MPC 使用同一套数据结构。
- 不在不同模块里重复定义字段名。

## 4. 阶段二：规则 Baseline

目的：在 MARL 之前先建立一个可解释、可运行、可对比的基线。

建议文件：

```text
src/core/cost_model.py
src/baseline/rule_assignment.py
examples/run_baseline.py
```

### 4.1 路径代价函数

第一版建议：

```text
path_cost =
    distance_cost
    + alpha * weather_cost
    + beta * altitude_change_cost
    + gamma * health_loss_cost
    + delta * energy_pressure
```

其中：

```text
health_loss_cost = 100 - dynamic_health_score
energy_pressure = normalize(pred_avg_current_a) + normalize(pred_voltage_drop_v)
```

初始参数：

```text
alpha = 1.0
beta = 0.3
gamma = 0.5
delta = 0.5
```

### 4.2 任务分配评分

第一版建议：

```text
assignment_score =
    dynamic_health_score
    - 20 * weather_cost
    - 10 * normalized_distance
    - 10 * normalized_payload
    - risk_penalty
```

风险惩罚：

```text
low    -> 0
medium -> 15
high   -> 100 或直接不可用
```

验收标准：

- 输入一组 UAV 和任务点，能输出任务分配结果。
- 输出每个任务的候选无人机评分。
- 输出总距离、总气象代价、总画像风险。
- 结果可复现，作为 MARL 对照组。

## 5. 阶段三：MARL 环境设计

建议文件：

```text
src/marl/env.py
src/marl/reward.py
```

### 5.1 Agent

```text
每架无人机是一个 agent。
```

### 5.2 State

每个 agent 的观测建议包括：

```text
current_lat
current_lon
current_height_m
dynamic_health_score
dynamic_risk_level_encoded
pred_avg_current_a
pred_voltage_drop_v
pred_stability_risk
nearby_weather_cost
nearby_wind_speed
nearby_wind_direction
distance_to_candidate_tasks
payload_demand_of_candidate_tasks
task_completion_mask
```

集中训练时可加入全局状态：

```text
all_uav_positions
all_task_status
global_weather_summary
remaining_task_count
```

### 5.3 Action

第一版可简化为离散动作：

```text
选择一个未完成任务
等待
返航
```

后续增强为：

```text
选择下一航点
选择高度层
选择避让方向
```

### 5.4 Reward

建议奖励函数：

```text
reward =
    task_complete_reward
    - distance_penalty
    - weather_penalty
    - energy_penalty
    - risk_penalty
    - conflict_penalty
    - timeout_penalty
```

建议初始权重：

```text
task_complete_reward = +100
distance_penalty = 1.0 * normalized_distance
weather_penalty = 20.0 * weather_cost
energy_penalty = 5.0 * energy_pressure
risk_penalty = 0 / 15 / 100
conflict_penalty = 50
timeout_penalty = 20
```

验收标准：

- 环境能 `reset()`。
- 环境能 `step(actions)`。
- 每一步返回 observations、rewards、done、info。
- info 中记录路径代价、气象代价、任务完成情况。

## 6. 阶段四：MARL 算法实现

建议优先实现：

```text
MAPPO
```

原因：

- 适合多智能体协作。
- 支持集中训练、分散执行。
- 适合解释为机群联合优化。

建议文件：

```text
src/marl/train_mappo.py
src/marl/policy.py
examples/run_marl_eval.py
```

第一版训练任务：

- 固定 3 到 5 架无人机。
- 固定 5 到 10 个任务点。
- 使用 24 小时样本气象地图。
- 使用 PyTorch Mamba 风格动态画像。
- 与规则 baseline 做对比。

验收标准：

- 能完成一次训练或模拟推理。
- 能输出每架无人机的任务分配。
- 能输出 MARL 的总代价和任务完成率。
- 能和 baseline 进行指标对比。

## 7. 阶段五：Robust MPC 轨迹跟踪

建议文件：

```text
src/mpc/dynamics.py
src/mpc/wind_model.py
src/mpc/robust_mpc.py
examples/run_mpc_tracking.py
```

### 7.1 输入

来自 MARL 的结果：

```text
uav_id
assigned_task_id
reference_waypoints
target_height_m
```

来自气象地图：

```text
wind_speed
wind_direction
weather_cost
```

### 7.2 输出

```text
corrected_trajectory
control_sequence
tracking_error
disturbance_rejection_score
```

### 7.3 第一版模型

可先使用简化三维点质量模型：

```text
state = [x, y, z, vx, vy, vz]
control = [ax, ay, az]
disturbance = wind_vector
```

约束：

```text
速度上限
加速度上限
高度层限制
最大航迹偏差
高 weather_cost 区域惩罚
```

验收标准：

- 给定参考航点，能生成平滑轨迹。
- 加入风扰后，MPC 能修正偏差。
- 能输出跟踪误差曲线。

## 8. 阶段六：评估指标

建议文件：

```text
src/eval/metrics.py
src/eval/compare_baseline_marl.py
```

必须统计：

```text
task_completion_rate
total_path_cost
average_weather_cost
total_distance
average_dynamic_health_score
high_risk_assignment_count
energy_pressure_sum
average_completion_time
uav_conflict_count
mpc_tracking_error
```

对比实验：

```text
规则 baseline
MARL without profile
MARL without weather
MARL with weather + profile
MARL + Robust MPC
```

验收标准：

- 能生成表格对比结果。
- 能说明气象地图和个体画像分别带来的提升。
- 能说明 MPC 对风扰跟踪误差的改善。

## 9. 阶段七：可视化与平台展示

建议文件：

```text
src/viz/plot_weather_map.py
src/viz/plot_routes.py
```

展示内容：

- 气象代价热力图。
- 10m / 100m 高度层切换。
- 无人机当前位置和画像状态。
- 任务点。
- baseline 路径。
- MARL 路径。
- MPC 修正轨迹。
- 风险与能耗曲线。

验收标准：

- 能直观看到高气象代价区域被规避。
- 能看到不同无人机因画像差异被分配不同任务。
- 能看到 MPC 修正前后轨迹差异。

## 10. Mamba 画像优化支线

这条线后续推进，不作为第一阶段 MARL 的阻塞项。

当前情况：

- `mamba_uav_dynamic_profiles.csv` 是 Mamba-lite 输出。
- `torch_mamba_uav_dynamic_profiles.csv` 是 PyTorch Mamba 风格输出。
- 二者都不是官方 `mamba-ssm` 完整版本。

后续任务：

- 安装并验证 `mamba-ssm`。
- 将 `SelectiveStateSpaceBlock` 替换为官方 Mamba block。
- 将 `Ridge Head` 或简单回归头升级为 MLP 多任务预测头。
- 增加剩余可飞行时间预测。
- 将 `dynamic_health_score` 从规则融合改为可学习输出。
- 重新生成动态画像 CSV，为 MARL 提供更强输入。

注意：

```text
正式重新训练需要完整 UAV_datas，本交接包当前没有包含完整 UAV_datas。
```

## 11. 推荐开发顺序

严格建议按以下顺序推进：

```text
1. 数据读取与统一接口
2. 规则 baseline
3. 路径代价函数
4. MARL 环境
5. MAPPO 训练与推理
6. baseline 与 MARL 对比
7. Robust MPC 轨迹跟踪
8. MARL + MPC 联合仿真
9. 可视化展示
10. 正式 Mamba 画像优化
```

不要一开始就同时写 MARL、MPC 和正式 Mamba。先跑通最小闭环：

```text
气象 cost + 动态画像 -> baseline/MARL 分配 -> 路径结果 -> 指标评估
```

## 12. 第一阶段最小可交付版本

第一阶段完成后，至少应具备：

- 能读取气象地图和无人机画像。
- 能查询任意候选任务点的气象代价。
- 能基于动态画像筛选无人机。
- 能运行规则 baseline。
- 能运行一个简化 MARL 环境。
- 能输出无人机到任务的分配结果。
- 能统计 baseline 与 MARL 的基本指标。

第一阶段不强制包含：

- 正式官方 Mamba 重训。
- 完整真实飞控接口。
- 高精度三维动力学。
- 大规模城市级地图。

## 13. 风险与注意事项

- 气象地图当前是原型数据，来自稀疏地区代表点和 IDW 插值，不应声称为最终科研级气象建模结果。
- Mamba-lite 不是正式官方 Mamba，应表述为“可用的动态画像原型”。
- MARL 需要先有稳定环境接口，否则训练结果不可解释。
- Robust MPC 应先做仿真级轨迹跟踪，再考虑真实控制接口。
- 所有结果必须和 baseline 对比，否则难以证明 MARL 的价值。

## 14. 建议论文或报告中的系统表述

可采用如下表述：

```text
本系统基于三维动态气象代价地图和无人机个体动态画像，构建面向多无人机任务分配与路径规划的多智能体强化学习环境。MARL 模块在全局层面学习气象风险、个体能力与任务收益之间的联合匹配策略；Robust MPC 模块在局部层面对 MARL 输出的参考航迹进行抗风扰跟踪控制，从而兼顾机群作业效率、飞行安全性与无人机健康损耗。
```

