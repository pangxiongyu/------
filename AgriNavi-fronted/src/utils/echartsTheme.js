import * as echarts from 'echarts';
function registerechartstheme() {
  echarts.registerTheme('mambaAgri', {
    color: ['#10B981', '#059669', '#34D399', '#6EE7B7', '#A7F3D0'],
    backgroundColor: 'transparent',
    textStyle: {
      fontFamily: "'Inter', 'Noto Sans SC', 'Microsoft YaHei', sans-serif"
    },
    title: {
      textStyle: {
        color: '#1a1a2e',
        fontSize: 16,
        fontWeight: 600
      }
    },
    legend: {
      textStyle: {
        color: '#6b7280',
        fontSize: 12
      }
    },
    tooltip: {
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#1a1a2e',
        fontSize: 13
      }
    },
    categoryAxis: {
      axisLine: {
        lineStyle: {
          color: '#d1d5db'
        }
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11
      },
      splitLine: {
        show: false
      }
    },
    valueAxis: {
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#9ca3af',
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed'
        }
      }
    },
    radar: {
      axisLine: {
        lineStyle: {
          color: '#d1d5db'
        }
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6'
        }
      },
      splitArea: {
        areaStyle: {
          color: ['#fff', '#f9fafb']
        }
      }
    }
  });
}
export { registerechartstheme };
