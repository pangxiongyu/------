import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { energyconsumptiondata } from '../../data/chartData';
export default function EnergyBarChart() {
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
      data: energyconsumptiondata.categories,
      axisLabel: {
        color: '#9CA3AF',
        fontSize: 10,
        rotate: 15
      },
      axisLine: {
        lineStyle: {
          color: '#E5E7EB'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '能耗 (kWh)',
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
      type: 'bar',
      data: energyconsumptiondata.ourAlgorithm,
      itemStyle: {
        color: '#10B981',
        borderRadius: [6, 6, 0, 0]
      },
      barWidth: '35%'
    }, {
      name: '传统算法',
      type: 'bar',
      data: energyconsumptiondata.traditional,
      itemStyle: {
        color: '#D1D5DB',
        borderRadius: [6, 6, 0, 0]
      },
      barWidth: '35%'
    }]
  }), []);
  return <ReactECharts option={option} style={{
    height: '350px'
  }} theme="mambaAgri" />;
}
