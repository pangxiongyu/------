import { HiGlobe, HiMap, HiDatabase, HiLightningBolt } from 'react-icons/hi'

export const TECH_FEATURES = [
  {
    title: 'GAT 图注意力网络',
    description: '基于图注意力机制的多机协同决策模型，实时感知农田拓扑结构变化，自适应调整飞行编队策略。',
    icon: 'network',
    gradient: 'from-emerald-500 to-teal-600',
  },
  {
    title: 'Mamba-MPSO 优化算法',
    description: '融合状态空间模型与多目标粒子群优化的路径规划引擎，在复杂山地实现最优航迹计算。',
    icon: 'algorithm',
    gradient: 'from-blue-500 to-indigo-600',
  },
  {
    title: '强化学习 / 多目标优化',
    description: '深度强化学习驱动自适应决策，同时优化能耗、覆盖率、时间效率等多维目标约束。',
    icon: 'brain',
    gradient: 'from-purple-500 to-violet-600',
  },
  {
    title: 'WebGL 三维渲染引擎',
    description: '基于 Three.js 的高性能三维地形可视化引擎，支持大规模点云实时渲染与飞行轨迹回放。',
    icon: 'cube',
    gradient: 'from-amber-500 to-orange-600',
  },
]

export const STATS = [
  { value: 500, suffix: '+', label: '农场覆盖', icon: HiGlobe },
  { value: 300, suffix: '+', label: '路径优化次数', icon: HiMap },
  { value: 1000, suffix: '+', label: '实时数据监测点', icon: HiDatabase },
  { value: 98, suffix: '+', label: '可视化响应率 %', icon: HiLightningBolt },
]
