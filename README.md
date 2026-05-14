# MambaAgriSim — 智慧农业无人机协同系统

基于 **React + Three.js + ECharts** 的三维可视化平台，实现多无人机协同路径规划、实时状态监控与智能农业应用集成。

![](https://img.shields.io/badge/React-18-blue?logo=react)
![](https://img.shields.io/badge/Three.js-0.165-green?logo=threedotjs)
![](https://img.shields.io/badge/ECharts-5.5-red?logo=apacheecharts)
![](https://img.shields.io/badge/Tailwind-3.4-06B6D4?logo=tailwindcss)
![](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite)

---

## 功能特性

- **智能路径规划** — Mamba-MPSO 优化算法驱动多机协同航迹计算
- **三维地形可视化** — Three.js 高性能渲染，支持实时飞行轨迹回放
- **数据仪表盘** — ECharts 多维度展示效率、能耗、任务完成度
- **农业应用矩阵** — 覆盖作物监测、病虫害预警、精准施肥等 8 大场景
- **UI 精装修** — 玻璃拟态、渐变发光边框、粒子背景、微动画

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/pangxiongyu/------.git
cd ------./mamba-agri-sim

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 生产构建
npm run build
```

## 项目结构

```
mamba-agri-sim/
├── src/
│   ├── components/
│   │   ├── common/          # 通用组件 (GlassCard, Navbar, SectionTitle...)
│   │   ├── homepage/        # 首页模块 (HeroBanner, TechFeatures, StatsGrid)
│   │   ├── charts/          # 图表组件 (ECharts)
│   │   └── viewport-3d/     # 三维视口 (Three.js)
│   ├── pages/               # 页面 (7 个路由)
│   ├── data/                # 数据配置
│   ├── context/             # React Context 状态管理
│   ├── hooks/               # 自定义 Hooks
│   └── utils/               # 工具函数
├── tailwind.config.js
├── vite.config.js
└── package.json
```

## 参与贡献

欢迎提交 Issue 和 Pull Request！

1. **Fork** 本仓库
2. 创建你的特性分支：`git checkout -b feature/amazing-feature`
3. 提交你的更改：`git commit -m 'feat: add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 发起 **Pull Request**

### 提交规范

推荐使用 [Conventional Commits](https://www.conventionalcommits.org/)：
- `feat:` 新功能
- `fix:` 修复 bug
- `style:` UI 样式调整
- `refactor:` 重构
- `docs:` 文档更新

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18 |
| 3D 渲染 | Three.js + @react-three/fiber + @react-three/drei |
| 图表 | ECharts 5 + echarts-for-react |
| 样式 | Tailwind CSS 3.4 + 自定义动画 |
| 动画 | Framer Motion 11 |
| 路由 | React Router 6 |
| 构建 | Vite 5 |

## License

MIT
