# Mamba-lite 无人机动态画像说明

本目录中的 Mamba-lite 版本由 `build_mamba_uav_profiles.py` 生成。

## 1. 为什么叫 Mamba-lite

当前本机环境未安装 PyTorch 和 `mamba-ssm`，因此本版本没有直接使用官方 Mamba 包。

但它保留了 Mamba/状态空间模型的核心工程思路：

```text
输入时序窗口 -> 选择性状态空间扫描 -> 时序特征编码 -> 预测未来状态风险
```

状态更新形式：

```text
h_t = gate(x_t) * (A * h_{t-1} + B * x_t)
```

这个版本的目标是先完成项目链路：

- 从真实无人机飞行时序数据中提取动态能力画像。
- 给路径规划模块提供“当前状态下是否适合承担任务”的评分。
- 给后续正式 Mamba/PyTorch 版本保留一致的数据接口。

## 2. 生成文件

- `mamba_uav_dynamic_profiles.csv`
  - 窗口级动态画像结果。
  - 每一行代表某次飞行中的一个时序窗口。

- `mamba_lite_metrics.json`
  - 训练/测试划分、窗口大小、预测目标和测试指标。

## 3. 输入特征

模型读取以下时序特征：

```text
wind_speed
battery_voltage
battery_current
velocity_x, velocity_y, velocity_z
angular_x, angular_y, angular_z
linear_acceleration_x, linear_acceleration_y, linear_acceleration_z
position_z
```

## 4. 预测目标

当前预测 3 个短时未来指标：

| 目标 | 含义 |
| --- | --- |
| `future_voltage_drop_v` | 未来短窗口内的电压下降 |
| `future_avg_current_a` | 未来短窗口内的平均电流 |
| `future_stability_risk` | 未来短窗口内的稳定性风险 |

当前配置：

```text
WINDOW_SIZE = 60
PREDICTION_HORIZON = 30
STRIDE = 30
```

可理解为：用前 60 个采样点预测后 30 个采样点的风险。

## 5. 输出字段

`mamba_uav_dynamic_profiles.csv` 字段：

| 字段 | 含义 |
| --- | --- |
| `flight_id` | 飞行编号 |
| `route` | 路线 |
| `payload_g` | 载重 |
| `target_altitude_m` | 预设高度 |
| `window_start_s` | 窗口开始时间 |
| `window_end_s` | 窗口结束时间 |
| `pred_voltage_drop_v` | 预测未来电压下降 |
| `pred_avg_current_a` | 预测未来平均电流 |
| `pred_stability_risk` | 预测未来稳定性风险，0-1 |
| `pred_stability_pressure` | 稳定性压力，0-100 |
| `dynamic_health_score` | 动态健康分，0-100，越高越适合承担任务 |
| `dynamic_risk_level` | 动态风险等级，low / medium / high |

## 6. 路径规划侧如何使用

路径规划模块可以读取：

```text
dynamic_health_score
dynamic_risk_level
pred_avg_current_a
pred_voltage_drop_v
```

建议用法：

```text
task_assignment_score =
    dynamic_health_score
    - 20 * weather_cost
    - 10 * normalized_payload
    - 10 * normalized_distance
```

如果某个窗口的 `dynamic_risk_level = high`，说明该状态下无人机不适合承担高风阻、长距离或高载重任务。

## 7. 当前测试指标

见 `mamba_lite_metrics.json`。

当前测试集指标大致表现：

- 未来平均电流预测效果较好。
- 稳定性风险预测有一定参考价值。
- 电压下降预测可以作为初版弱指标，后续需要更长序列或更强模型提升。

## 8. 后续升级为正式 Mamba

后续如果安装 PyTorch 和 `mamba-ssm`，可以保留当前数据窗口生成逻辑，只替换模型部分：

```text
Mamba-lite Encoder -> Official Mamba Block
Ridge Head -> MLP Regression Head
```

推荐升级方向：

- 使用 PyTorch Dataset/DataLoader。
- 使用 Mamba block 编码完整飞行序列。
- 多任务预测：电压下降、电流、稳定性风险、剩余可飞行时间。
- 将 `dynamic_health_score` 从规则融合改为可学习输出。

