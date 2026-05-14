export const SUMMARY_CARDS = [
  { title: '路径效率', value: '92%', trend: '+5.2%', up: true, color: 'text-agri-500' },
  { title: '能耗变化', value: '-15%', trend: '↓ 3.8%', up: true, color: 'text-blue-500' },
  { title: '喷洒成功率', value: '97%', trend: '+2.1%', up: true, color: 'text-agri-600' },
]

export const pathEfficiencyData = {
  months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  ourAlgorithm: [85, 87, 89, 90, 91, 92, 93, 94, 93, 95, 96, 95],
  traditional: [72, 74, 75, 73, 76, 78, 77, 79, 80, 78, 81, 80],
}

export const energyConsumptionData = {
  categories: ['巡检任务', '喷洒作业', '测绘任务', '运输任务', '播种任务', '监测任务'],
  ourAlgorithm: [23, 45, 18, 32, 28, 15],
  traditional: [35, 62, 28, 45, 40, 22],
}

export const performanceRadarData = {
  indicators: [
    { name: '路径效率', max: 100 },
    { name: '覆盖完整度', max: 100 },
    { name: '能耗控制', max: 100 },
    { name: '环境适应', max: 100 },
    { name: '执行速度', max: 100 },
    { name: '协同能力', max: 100 },
  ],
  ourAlgorithm: [92, 88, 85, 90, 87, 93],
  traditional: [75, 70, 68, 72, 78, 65],
}

export const taskCompletionData = [
  { name: '已完成', value: 65, itemStyle: { color: '#10B981' } },
  { name: '进行中', value: 20, itemStyle: { color: '#3B82F6' } },
  { name: '待分配', value: 10, itemStyle: { color: '#F59E0B' } },
  { name: '失败', value: 5, itemStyle: { color: '#EF4444' } },
]

export const taskTrendData = {
  months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  completed: [42, 48, 55, 52, 60, 58, 65, 70, 68, 72, 75, 78],
  total: [50, 55, 62, 60, 68, 65, 72, 76, 74, 78, 80, 82],
}
