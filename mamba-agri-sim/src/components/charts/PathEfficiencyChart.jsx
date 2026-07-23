import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { pathefficiencydata } from '../../data/chartData';
export default function PathEfficiencyChart() {
  const option = useMemo(() => ({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['本系统算法', '传统算法'],
      bottom: 0,
      textStyle: {
        color: '#6B7280',
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: pathefficiencydata.months,
      axisLabel: {
        color: '#9CA3AF'
      },
      axisLine: {
        lineStyle: {
          color: '#E5E7EB'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '效率 (%)',
      min: 60,
      max: 100,
      axisLabel: {
        color: '#9CA3AF'
      },
      splitLine: {
        lineStyle: {
          color: '#F3F4F6',
          type: 'dashed'
        }
      }
    },
    series: [{
      name: '本系统算法',
      type: 'line',
      data: pathefficiencydata.ourAlgorithm,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        color: '#10B981',
        width: 3
      },
      itemStyle: {
        color: '#10B981'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0,
            color: 'rgba(16,185,129,0.3)'
          }, {
            offset: 1,
            color: 'rgba(16,185,129,0.02)'
          }]
        }
      }
    }, {
      name: '传统算法',
      type: 'line',
      data: pathefficiencydata.traditional,
      smooth: true,
      symbol: 'diamond',
      symbolSize: 6,
      lineStyle: {
        color: '#9CA3AF',
        width: 2,
        type: 'dashed'
      },
      itemStyle: {
        color: '#9CA3AF'
      }
    }]
  }), []);
  return <ReactECharts option={option} style={{
    height: '350px'
  }} theme="mambaAgri" />;
}
