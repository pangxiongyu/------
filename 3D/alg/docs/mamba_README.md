# PyTorch Mamba 风格无人机动态画像

本版本由 `build_torch_mamba_uav_profiles.py` 生成，运行环境为 conda `py311`。

## 运行命令

```bash
conda run -n py311 python build_torch_mamba_uav_profiles.py
```

如果在 Cursor 终端里运行 PyTorch/MPS 出现动态库或段错误，建议直接使用本机终端运行以上命令。

## 版本说明

当前脚本会优先尝试使用官方 `mamba-ssm` 包；如果当前环境没有安装官方包，则自动回退到 PyTorch 实现的 **Mamba 风格选择性状态空间块**：

```text
输入时序窗口
-> Linear Projection
-> Selective State-Space Scan Blocks
-> Last Pooling + Mean Pooling
-> Multi-task Regression Head
```

它不是官方 Mamba，但已经是可训练的 PyTorch 神经网络，后续可以比较容易替换为官方 Mamba block。

## 输入特征

模型使用以下无人机飞行时序特征：

```text
wind_speed
battery_voltage
battery_current
velocity_x, velocity_y, velocity_z
angular_x, angular_y, angular_z
linear_acceleration_x, linear_acceleration_y, linear_acceleration_z
position_z
```

## 预测目标

模型使用当前 60 个采样点预测未来 30 个采样点的状态：

| 输出目标 | 含义 |
| --- | --- |
| `future_voltage_drop_v` | 未来电压下降 |
| `future_avg_current_a` | 未来平均电流 |
| `future_stability_risk` | 未来稳定性风险 |

## 输出文件

- `torch_mamba_uav_dynamic_profiles.csv`
  - 路径规划和可视化优先使用这个文件。

- `mamba_uav_dynamic_profiles_official.csv`
  - 与 `torch_mamba_uav_dynamic_profiles.csv` 字段一致。
  - 当前 `configs/default.yaml` 默认读取该文件，作为项目书口径下的 Mamba 画像接口。

- `torch_mamba_metrics.json`
  - 训练配置、Mamba 后端、测试指标、loss 曲线。

- `torch_mamba_uav_profile_model.pt`
  - PyTorch 模型权重与标准化参数。

## 主要输出字段

| 字段 | 含义 |
| --- | --- |
| `flight_id` | 飞行编号 |
| `route` | 路线 |
| `payload_g` | 载重 |
| `target_altitude_m` | 目标高度 |
| `window_start_s` | 窗口开始时间 |
| `window_end_s` | 窗口结束时间 |
| `pred_voltage_drop_v` | 预测未来电压下降 |
| `pred_avg_current_a` | 预测未来平均电流 |
| `pred_stability_risk` | 预测未来稳定性风险 |
| `dynamic_health_score` | 动态健康分，越高越适合承担任务 |
| `dynamic_risk_level` | 动态风险等级，low / medium / high |

## 当前测试效果

本次训练生成了 8076 个时序窗口，训练集 6555 个，测试集 1521 个。

测试集指标见 `torch_mamba_metrics.json`，当前大致为：

- 未来电压下降：`R² ≈ 0.46`
- 未来平均电流：`R² ≈ 0.96`
- 未来稳定性风险：`R² ≈ 0.72`

## 路径规划侧使用建议

路径规划可以读取：

```text
dynamic_health_score
dynamic_risk_level
pred_avg_current_a
pred_voltage_drop_v
```

示例：

```text
assignment_score =
    dynamic_health_score
    - 20 * weather_cost
    - 10 * payload_difficulty
    - 10 * distance_difficulty
```

如果 `dynamic_risk_level = high`，说明该窗口对应的无人机状态不适合承担高风阻、高载重或长距离任务。

## 官方 Mamba 后端

如果安装 `mamba-ssm`，脚本会自动使用官方 Mamba block。未安装时，脚本使用 `SelectiveStateSpaceBlock` 回退后端。两种后端保持相同 CSV 输出接口：

- 数据窗口生成逻辑
- 标准化逻辑
- 多任务预测目标
- CSV 输出格式
- 路径规划接口

