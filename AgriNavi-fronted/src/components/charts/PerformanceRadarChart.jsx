import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { performanceradardata } from '../../data/chartData';
export default function PerformanceRadarChart() {
  const option = useMemo(() => ({
    tooltip: {},
    legend: {
      data: ['本系统算法', '传统算法'],
      bottom: 0,
      textStyle: {
        color: '#6B7280',
        fontSize: 12
      }
    },
    radar: {
      indicator: performanceradardata.indicators,
      shape: 'circle',
      splitNumber: 4,
      axisName: {
        color: '#6B7280',
        fontSize: 11
      }
    },
    series: [{
      type: 'radar',
      data: [{
        name: '本系统算法',
        value: performanceradardata.ourAlgorithm,
        lineStyle: {
          color: '#10B981',
          width: 2
        },
        areaStyle: {
          color: 'rgba(16,185,129,0.2)'
        },
        itemStyle: {
          color: '#10B981'
        },
        symbol: 'circle',
        symbolSize: 5
      }, {
        name: '传统算法',
        value: performanceradardata.traditional,
        lineStyle: {
          color: '#9CA3AF',
          width: 2
        },
        areaStyle: {
          color: 'rgba(156,163,175,0.1)'
        },
        itemStyle: {
          color: '#9CA3AF'
        },
        symbol: 'diamond',
        symbolSize: 4
      }]
    }]
  }), []);
  return <ReactECharts option={option} style={{
    height: '350px'
  }} theme="mambaAgri" />;
}
