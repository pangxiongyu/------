# 三维动态气象代价地图原型数据

本目录由 `build_weather_cost_map.py` 生成，用于项目第一版 Web/QT 可视化和算法联调。

## 文件说明

- `weather_cost_map_prototype.csv`
  - 完整原型数据。
  - 基于 `output_data/*.csv` 生成。
  - 适合算法读取，不建议前端直接一次性加载。

- `weather_cost_map_sample_24h.csv`
  - 前 24 小时样本数据。
  - 适合 Web/QT 首版展示与调试。

## 字段说明

| 字段 | 含义 |
| --- | --- |
| `time` | 时间戳 |
| `latitude` | 插值网格点纬度 |
| `longitude` | 插值网格点经度 |
| `height_m` | 高度层，目前为 10m 和 100m |
| `cost` | 气象代价，范围约为 0-1，越大表示飞行风险/损耗越高 |
| `wind_speed` | 插值后的风速 |
| `wind_direction` | 插值后的风向 |
| `temperature_2m` | 2m 温度 |
| `relative_humidity_2m` | 2m 相对湿度 |
| `weather_code` | 天气类型编码 |

## 建模假设

由于现有 `output_data` 没有精确经纬度字段，本版本采用地区代表点作为稀疏观测点，并通过 IDW（反距离加权）插值生成网格化代价地图。

本版本适合用于：

- 跑通“三维动态代价地图”的数据格式。
- 给 Web/QT 做热力图、三维点云、时间滑块展示。
- 给后续路径规划模块提供初始环境代价输入。

本版本不适合作为最终科研级气象建模结果。后续建议替换为 ERA5 / Open-Meteo 多网格点 / 探空数据。

## 代价函数

当前原型代价函数：

```text
cost = 0.52 * wind_cost
     + 0.24 * gust_cost
     + 0.14 * humidity_cost
     + 0.10 * weather_code_penalty
```

后续可以根据无人机飞行日志 `UAV_datas` 中的电池电流、姿态扰动、风速等变量校准这些权重。
