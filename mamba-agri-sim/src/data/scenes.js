export const SCENES = [
  {
    id: 'modern',
    name: '现代平原果园',
    shortName: '平原果园',
    icon: '🍎',
    badge: '网格化果树作业场景',
    acreage: '140 亩',
    terrain: '平原缓坡 + 十字主作业道',
    crop: '苹果 / 桃类果树',
    altitude: '25-50 m',
    wind: '作业层 70m，默认 6.8 m/s',
    summary: '适合展示标准果园的多机起降、任务点布设、路径匹配与低空风场能耗评估。',
    highlights: ['十字形作业道', '规则果树行阵列', '低坡度起降区域', '多机并行任务'],
    focusLayerId: 'operation',
    planning: {
      droneCount: 2,
      taskCount: 3,
      placement: '中心停机坪起飞，沿果树行点击设置任务点',
      assignment: '最近距离自动匹配任务',
    },
    energy: {
      initialBatteryPercent: 100,
      baseConsumptionPerMeter: 0.035,
      windSensitivity: 0.0015,
    },
    params: {
      start: '中心停机坪',
      task: '果树行巡检 / 喷洒',
      risk: '低至中',
      route: '网格航线优先',
    },
  },
  {
    id: 'terrace',
    name: '高山梯田农场',
    shortName: '高山梯田',
    icon: '🌾',
    badge: '高差复杂农田场景',
    acreage: '96 亩',
    terrain: '垂直高差 + 阶梯田埂',
    crop: '水稻 / 梯田作物',
    altitude: '70-135 m',
    wind: '高空层 115m，默认 10.5 m/s',
    summary: '适合展示复杂海拔变化下的起降点约束、三维路径高度切换与风场附加能耗。',
    highlights: ['阶梯式高差', '田埂边缘约束', '高风速层影响', '三维高度规划'],
    focusLayerId: 'upper',
    planning: {
      droneCount: 2,
      taskCount: 3,
      placement: '优先选择平坦田面，避开陡峭田埂边缘',
      assignment: '最近距离匹配，并叠加高度代价判断',
    },
    energy: {
      initialBatteryPercent: 100,
      baseConsumptionPerMeter: 0.035,
      windSensitivity: 0.0015,
    },
    params: {
      start: '平坦田面起降',
      task: '梯田分层巡检 / 喷洒',
      risk: '中至高',
      route: '高度代价约束',
    },
  },
]

export const WIND_LAYERS = [
  {
    id: 'near-ground',
    label: '近地层',
    height: 35,
    speed: 3.2,
    direction: 45,
    color: '#4caf50',
    note: '低空作业扰动较小',
  },
  {
    id: 'operation',
    label: '作业层',
    height: 70,
    speed: 6.8,
    direction: 110,
    color: '#ffb300',
    note: '无人机主要巡航高度',
  },
  {
    id: 'upper',
    label: '高空层',
    height: 115,
    speed: 10.5,
    direction: 230,
    color: '#e53935',
    note: '风速较大，路径代价更高',
  },
]

SCENES.forEach((scene) => {
  scene.windLayers = WIND_LAYERS
})

export const DEFAULT_SCENE_ID = 'modern'

export function getSceneById(id) {
  return SCENES.find((scene) => scene.id === id) ?? SCENES[0]
}
