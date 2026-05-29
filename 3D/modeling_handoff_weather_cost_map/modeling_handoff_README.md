# 路径规划建模交接说明

本交接包用于将当前已完成的气象建模原型交给路径规划模块使用。

## 1. 包内核心内容

建议路径规划侧优先读取：

- `generated_weather_cost_map/weather_cost_map_sample_24h.csv`
  - 24 小时样本数据，适合先调试路径规划读取逻辑和可视化。

- `generated_weather_cost_map/weather_cost_map_prototype.csv`
  - 完整原型数据，适合正式跑批量实验。

- `build_weather_cost_map.py`
  - 代价地图生成脚本。后续如果更换 ERA5 / Open-Meteo 数据，可以在这个脚本基础上改。

- `output_data/`
  - 当前使用的原始气象数据。

## 2. 代价地图字段

CSV 字段如下：

```text
time, latitude, longitude, height_m, cost, wind_speed, wind_direction, temperature_2m, relative_humidity_2m, weather_code
```

字段含义：

- `time`：时间戳。
- `latitude` / `longitude`：网格点经纬度。
- `height_m`：高度层，目前为 `10` 和 `100`。
- `cost`：气象代价，范围约为 `0-1`，越大表示飞行风险或损耗越高。
- `wind_speed`：插值后的风速。
- `wind_direction`：插值后的风向。
- `temperature_2m`：2m 温度。
- `relative_humidity_2m`：2m 相对湿度。
- `weather_code`：天气类型编码。

## 3. 路径规划侧推荐使用方式

路径规划模块可以将 `cost` 作为环境代价项，加入路径搜索或强化学习 reward。

例如：

```text
total_cost = distance_cost
           + alpha * weather_cost
           + beta * altitude_change_cost
           + gamma * battery_cost
```

其中：

- `weather_cost` 可以直接来自 CSV 的 `cost`。
- `alpha` 是气象风险权重，第一版可以从 `0.3 - 1.0` 之间调参。
- 如果路径规划只有二维地图，可以先固定 `height_m = 10`。
- 如果路径规划支持三维航迹，可以按无人机飞行高度选择最近的 `height_m` 层，或在 `10m/100m` 之间做线性插值。

## 4. 当前版本建模假设

当前版本是原型，不是最终科研级气象场。

主要假设：

- 使用 `output_data` 中的多个地区作为稀疏观测点。
- 对每个地区补充代表性经纬度。
- 使用 `10m` 和 `100m` 两个风场高度层构造准三维环境。
- 使用 IDW 反距离加权插值生成网格。
- 使用风速、阵风、湿度、天气类型构造气象代价。

代价函数为：

```text
cost = 0.52 * wind_cost
     + 0.24 * gust_cost
     + 0.14 * humidity_cost
     + 0.10 * weather_code_penalty
```

后续可以用 `UAV_datas` 中的飞行日志校准权重，比如根据电流消耗、姿态扰动和风速之间的关系调整代价函数。

## 5. 为什么没有默认打包完整 UAV_datas

`UAV_datas` 约 832MB，体积较大，主要用于：

- 电池消耗建模。
- 无人机个体画像。
- Mamba / LSTM / Transformer 时序预测。
- 风扰对姿态、速度、加速度影响分析。

如果路径规划侧需要接入无人机个体能耗模型，再单独传输 `UAV_datas` 更合适。

## 6. 快速重新生成代价地图

在项目根目录执行：

```bash
python3 build_weather_cost_map.py
```

输出目录：

```text
generated_weather_cost_map/
```

