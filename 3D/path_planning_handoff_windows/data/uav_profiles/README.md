# 无人机个体画像第一版

本目录由 `build_uav_profiles.py` 生成，用于项目第一版无人机能力评估、路径规划分配和 Web/QT 可视化展示。

## 文件说明

- `uav_profiles.csv`
  - 每一行代表一次飞行任务的画像结果。
  - 数据来源为 `UAV_datas/parameters.csv` 和 `UAV_datas/flights/*.csv`。

## 核心字段

| 字段 | 含义 |
| --- | --- |
| `flight_id` | 飞行编号 |
| `route` | 飞行路线 |
| `target_speed_mps` | 预设巡航速度 |
| `payload_g` | 载重，单位 g |
| `target_altitude_m` | 预设高度 |
| `duration_s` | 飞行持续时间 |
| `avg_wind_speed_mps` | 平均风速 |
| `max_wind_speed_mps` | 最大风速 |
| `avg_current_a` | 平均电流 |
| `max_current_a` | 最大电流 |
| `voltage_drop_v` | 电压下降 |
| `energy_wh` | 估算能耗，单位 Wh |
| `energy_per_min_wh` | 单位时间能耗 |
| `energy_per_meter_wh` | 单位距离近似能耗 |
| `speed_std` | 速度波动 |
| `vertical_speed_std` | 垂直速度波动 |
| `angular_mean` | 平均角速度扰动 |
| `acceleration_std` | 加速度波动 |
| `altitude_std_m` | 高度波动 |
| `wind_pressure` | 风扰压力评分，越高压力越大 |
| `energy_pressure` | 能耗压力评分，越高压力越大 |
| `stability_pressure` | 稳定性压力评分，越高压力越大 |
| `health_score` | 综合健康分，0-100，越高越适合承担任务 |
| `energy_efficiency_score` | 能耗效率分，越高越省电 |
| `capacity_grade` | 能力等级，A/B/C/D |
| `risk_level` | 风险等级，low/medium/high |

## 路径规划侧使用建议

路径规划可以把 `health_score` 和 `risk_level` 作为无人机分配约束。

示例：

```text
如果 weather_cost 较高：
    优先选择 health_score 高、capacity_grade 为 A/B 的无人机

如果任务距离较长：
    优先选择 energy_efficiency_score 高的无人机

如果任务载重较高：
    优先排除历史 max_current_a 过高、health_score 过低的样本
```

第一版可采用简单规则：

```text
uav_task_score = health_score
               - 20 * weather_cost
               - 10 * payload_difficulty
               - 10 * altitude_difficulty
```

## 当前版本说明

当前版本是“统计可解释版”，不是 Mamba 预测版。

它适合：

- 先跑通无人机画像到路径规划的接口。
- 在 Web/QT 中展示不同飞行任务的健康分、风险等级和能耗曲线。
- 为后续 Mamba 模型提供标签和基线特征。

## 后续升级方向

下一版可以升级为 Mamba 时序预测：

- 输入：一段时间窗口内的风速、电流、电压、速度、姿态、加速度序列。
- 输出：
  - 未来电压下降趋势。
  - 未来能耗。
  - 剩余可飞行时间。
  - 动态健康因子。

Mamba 版本可以把当前 `health_score` 作为弱标签或基线指标，用真实时序数据进一步学习。

