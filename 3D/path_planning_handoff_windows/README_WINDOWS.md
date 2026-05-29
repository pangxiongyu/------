# Path Planning Handoff Package

本压缩包用于交接给路径规划同学，内容包括：

- 三维动态气象代价地图
- 无人机统计画像
- PyTorch Mamba 风格动态无人机画像
- 数据生成脚本
- Windows 环境下的读取与接入说明

建议先使用已生成的 CSV 文件完成路径规划，不必一开始重新训练模型。

---

## 1. 推荐读取顺序

路径规划同学优先读取这两个文件：

```text
data/weather_cost_map/weather_cost_map_sample_24h.csv
data/uav_profiles/torch_mamba_uav_dynamic_profiles.csv
```

如果小样本跑通，再切换到完整气象地图：

```text
data/weather_cost_map/weather_cost_map_prototype.csv
```

---

## 2. 气象代价地图

文件：

```text
data/weather_cost_map/weather_cost_map_sample_24h.csv
data/weather_cost_map/weather_cost_map_prototype.csv
```

字段：

```text
time, latitude, longitude, height_m, cost, wind_speed, wind_direction,
temperature_2m, relative_humidity_2m, weather_code
```

路径规划最重要字段：

```text
cost
```

含义：

- `cost` 范围约为 `0-1`
- 越大表示气象风险/飞行损耗越高
- 当前高度层为 `10m` 和 `100m`
- 当前空间网格由现有气象数据通过 IDW 插值得到

推荐路径代价函数：

```text
path_cost = distance_cost
          + alpha * weather_cost
          + beta * altitude_change_cost
          + gamma * battery_or_health_cost
```

第一版建议：

```text
alpha = 0.5 ~ 1.5
beta = 0.1 ~ 0.5
gamma = 0.3 ~ 1.0
```

---

## 3. 无人机动态画像

优先使用 PyTorch 版结果：

```text
data/uav_profiles/torch_mamba_uav_dynamic_profiles.csv
```

字段：

```text
flight_id, route, payload_g, target_altitude_m,
window_start_s, window_end_s,
pred_voltage_drop_v, pred_avg_current_a, pred_stability_risk,
pred_stability_pressure, dynamic_health_score, dynamic_risk_level
```

路径规划最重要字段：

```text
dynamic_health_score
dynamic_risk_level
pred_avg_current_a
pred_voltage_drop_v
```

含义：

- `dynamic_health_score`：0-100，越高说明无人机状态越适合承担任务
- `dynamic_risk_level`：`low` / `medium` / `high`
- `pred_avg_current_a`：预测未来平均电流，可近似表示能耗压力
- `pred_voltage_drop_v`：预测未来电压下降

任务分配建议：

```text
assignment_score =
    dynamic_health_score
    - 20 * weather_cost
    - 10 * normalized_payload
    - 10 * normalized_distance
```

如果 `dynamic_risk_level = high`，建议不要分配高风阻、长距离或高载重任务。

---

## 4. Windows 环境建议

最低要求：

```text
Python >= 3.9
pandas
numpy
```

如果只是读取 CSV 做路径规划：

```bash
pip install pandas numpy
```

如果需要重新训练 PyTorch Mamba 风格画像：

```bash
pip install torch pandas numpy
```

Windows 上建议避免中文路径。可以将压缩包解压到：

```text
C:\uav_project\path_planning_handoff\
```

注意：`output_data/` 是原始气象数据，部分文件名包含中文地区名。路径规划同学一般不需要直接读取它；优先读取英文目录 `data/` 下的文件即可。如果 Windows 解压后原始文件名显示乱码，不影响 `data/weather_cost_map/` 和 `data/uav_profiles/` 的使用。

---

## 5. 快速读取示例

见：

```text
examples/read_handoff_data.py
```

运行：

```bash
python examples/read_handoff_data.py
```

---

## 6. 重新生成数据

如需重新生成气象代价地图：

```bash
python build_weather_cost_map.py
```

如需重新生成统计版无人机画像：

```bash
python build_uav_profiles.py
```

如需重新训练 PyTorch Mamba 风格画像：

```bash
python build_torch_mamba_uav_profiles.py
```

注意：重新训练 PyTorch 版需要完整 `UAV_datas` 原始飞行日志。本交接包默认不包含完整 `UAV_datas`，因为该目录约 832MB。

---

## 7. 当前包没有包含完整 UAV_datas 的原因

完整 `UAV_datas` 主要用于重新训练无人机画像模型，体积约 832MB。

路径规划同学当前只需要读取：

- 气象代价地图 CSV
- 已生成的无人机动态画像 CSV

因此本包只放结果和脚本。如果后续需要重新训练模型，请单独索取完整 `UAV_datas`。

