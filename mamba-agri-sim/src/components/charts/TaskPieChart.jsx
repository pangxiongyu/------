import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { taskCompletionData } from '../../data/chartData'

export default function TaskPieChart() {
  const option = useMemo(() => ({
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      textStyle: { color: '#6B7280', fontSize: 11 },
    },
    series: [{
      name: '任务状态',
      type: 'pie',
      radius: ['55%', '80%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 16, fontWeight: 'bold' },
        scaleSize: 8,
      },
      data: taskCompletionData,
    }],
  }), [])

  return <ReactECharts option={option} style={{ height: '350px' }} theme="mambaAgri" />
}
