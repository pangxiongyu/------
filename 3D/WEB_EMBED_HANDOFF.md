# Web 嵌入交接文档（给前端/平台同学）

本文档用于帮助队友把当前项目快速嵌入到网页中，并明确前端展示、算法数据导出与部署方式。

---

## 1. 项目结构与职责

以 `/Users/pordrick/Desktop/3D` 为根目录，核心目录如下：

- `drone-orchard/`：Web 前端工程（Vite + React + Three.js），负责 3D 可视化。
- `alg/`：算法与实验工程（Python + Conda），负责生成任务分配/航迹等数据。
- `path_planning_handoff_windows/`：交接版算法目录（文档和脚本较完整，可作参考）。
- `modeling_handoff_weather_cost_map/`：气象代价地图建模与输出。
- `UAV_datas/`：历史/原始无人机数据。

嵌入网页时，主要用到 `drone-orchard`（前端）+ `alg`（数据导出）。

---

## 2. Web 工程快速启动

### 2.1 本地开发

```bash
cd /Users/pordrick/Desktop/3D/drone-orchard
npm ci
npm run dev
```

说明：

- 开发入口文件：`drone-orchard/index.html`
- 应用入口：`drone-orchard/src/main.tsx`
- 目前 `vite.config.ts` 没有配置 `base` 和 `proxy`（默认站点根路径 `/`）

### 2.2 构建生产包

```bash
cd /Users/pordrick/Desktop/3D/drone-orchard
npm run build
npm run preview
```

构建产物目录：`drone-orchard/dist/`，可直接部署到静态服务器（Nginx、对象存储静态托管、GitHub Pages 等）。

---

## 3. 两种嵌入方式（按场景选）

## 方案 A：iframe 嵌入（最快）

适合快速接入、最小改造。

宿主页面示例：

```html
<iframe
  src="https://your-domain.com/drone-orchard/"
  style="width: 100%; height: 100vh; border: 0;"
  allow="fullscreen"
></iframe>
```

要求：

- `drone-orchard` 已独立部署可访问。
- 若部署在子路径（如 `/drone-orchard/`），需要在 `vite.config.ts` 中设置 `base: '/drone-orchard/'` 后重新构建。

## 方案 B：同站点静态集成（推荐长期）

适合主站统一域名和资源管理。

做法：

1. 构建 `drone-orchard/dist`。
2. 将 `dist` 内容拷贝到主站静态目录子路径（例如 `/apps/drone-orchard/`）。
3. 在主站路由中挂载该路径。
4. 若部署在子路径，配置 Vite `base` 后重建，避免资源 404。

---

## 4. 算法数据到 Web 的对接

当前仓库没有内置业务 API 服务，推荐先走“离线导出 -> 前端静态读取”。

### 4.1 算法侧导出航迹数据（CSV）

在 `alg` 中，`src/eval/export.py` 已提供 `export_route_waypoints_csv(...)`，字段如下：

- `method`
- `uav_id`
- `task_id`
- `leg_index`
- `route_strategy`
- `point_index`
- `latitude`
- `longitude`
- `height_m`
- `weather_cost`

该文件注释已明确：用于 Qt/Web 3D visualization。

### 4.2 一条可复现的导出命令

```bash
cd /Users/pordrick/Desktop/3D/alg
conda env create -f environment.yml   # 首次执行
conda activate torch_env
python examples/run_mappo_benchmark.py \
  --config configs/default.yaml \
  --checkpoint outputs/mappo_trackability_multiseed/track_w25_seed7_e40/best_checkpoint.pt \
  --output-dir outputs/gpr_mamba_mappo_benchmark
```

重点输出文件：

- `alg/outputs/gpr_mamba_mappo_benchmark/planned_routes_waypoints.csv`（Web 侧重点读取）
- `alg/outputs/gpr_mamba_mappo_benchmark/comparison.md`
- `alg/outputs/gpr_mamba_mappo_benchmark/mpc_tracking.csv`

### 4.3 前端接入建议

短期（推荐先做）：

1. 将 `planned_routes_waypoints.csv` 放入 Web 静态可访问路径（如 `public/data/`）。
2. 在前端新增 CSV 解析模块，按 `uav_id + leg_index + point_index` 组装航迹线。
3. 用 `height_m` 映射 3D 高度，用 `weather_cost` 做颜色/透明度映射（可选）。

中期（需要后端）：

- 增加一个轻量 API（如 `/api/routes/latest`）返回 JSON，前端定时拉取。
- 处理缓存、鉴权、CORS。

---

## 5. 交付给 Web 同学的最小清单

请按以下清单交接：

1. 前端工程：`drone-orchard/`
2. Web 构建产物：`drone-orchard/dist/`
3. 算法导出的航迹 CSV：`alg/outputs/gpr_mamba_mappo_benchmark/planned_routes_waypoints.csv`
4. 算法链路说明：`drone-orchard/FINAL_MODEL_ALGORITHM.md`
5. 最终交接说明：`alg/docs/PROJECT_FINAL_HANDOFF.md`

---

## 6. 常见问题（提前规避）

### 6.1 页面空白或资源 404

通常是 `base` 配置与部署路径不一致。部署在子路径时，必须设置 Vite `base` 后重建。

### 6.2 Web 端拿不到算法数据

当前默认不是 API 拉取模式。请先确认 CSV 文件已经放到前端可访问路径，并且浏览器网络面板可看到 200 响应。

### 6.3 跨域问题

若将 CSV/API 放在其他域名，需配置 CORS 或改为同域反向代理。

### 6.4 数据更新频率

如果是演示场景，建议按批次导出静态 CSV；如果是在线场景，再考虑 API + 定时刷新。

---

## 7. 推荐落地路径（执行顺序）

1. 先把 `drone-orchard` 独立部署并验证可访问。
2. 先用 iframe 接到主站，完成展示上线。
3. 再接 `planned_routes_waypoints.csv` 真数据，替换或增强现有演示轨迹。
4. 最后评估是否引入后端 API 做动态更新。

这样可以把“能展示”与“真数据联动”拆开，降低联调风险。

