import { useEffect } from 'react'
import { motion } from 'framer-motion'
import PageContainer from '../components/common/PageContainer'
import GlassCard from '../components/common/GlassCard'
import SectionTitle from '../components/common/SectionTitle'
import SummaryCards from '../components/charts/SummaryCards'
import PathEfficiencyChart from '../components/charts/PathEfficiencyChart'
import EnergyBarChart from '../components/charts/EnergyBarChart'
import PerformanceRadarChart from '../components/charts/PerformanceRadarChart'
import TaskPieChart from '../components/charts/TaskPieChart'
import { registerEchartsTheme } from '../utils/echartsTheme'

export default function DataDisplayPage() {
  useEffect(() => {
    registerEchartsTheme()
  }, [])

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto px-6 py-20">
        <SectionTitle
          badge="数据分析"
          title="数据可视化仪表盘"
          subtitle="多维度展示路径规划效率、能耗、任务完成度与环境适应能力"
        />

        {/* Summary cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <SummaryCards />
        </motion.div>

        {/* Charts row 1 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid lg:grid-cols-3 gap-6 mb-6"
        >
          <GlassCard variant="premium" className="lg:col-span-2 !p-7">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1.5 h-5 rounded-full bg-gradient-to-b from-agri-400 to-agri-600" />
              <h3 className="text-lg font-bold text-dark">路径规划效率趋势</h3>
              <span className="text-xs text-gray-400 ml-auto bg-gray-100 px-2.5 py-1 rounded-full">近30天</span>
            </div>
            <PathEfficiencyChart />
          </GlassCard>

          <GlassCard variant="premium" className="!p-7">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1.5 h-5 rounded-full bg-gradient-to-b from-amber-400 to-orange-500" />
              <h3 className="text-lg font-bold text-dark">任务完成分布</h3>
            </div>
            <TaskPieChart />
          </GlassCard>
        </motion.div>

        {/* Charts row 2 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="grid lg:grid-cols-3 gap-6"
        >
          <GlassCard variant="premium" className="lg:col-span-2 !p-7">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1.5 h-5 rounded-full bg-gradient-to-b from-purple-400 to-violet-600" />
              <h3 className="text-lg font-bold text-dark">多任务能耗对比</h3>
              <span className="text-xs text-gray-400 ml-auto bg-gray-100 px-2.5 py-1 rounded-full">kWh</span>
            </div>
            <EnergyBarChart />
          </GlassCard>

          <GlassCard variant="premium" className="!p-7">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1.5 h-5 rounded-full bg-gradient-to-b from-blue-400 to-indigo-600" />
              <h3 className="text-lg font-bold text-dark">多维性能评估</h3>
            </div>
            <PerformanceRadarChart />
          </GlassCard>
        </motion.div>
      </div>
    </PageContainer>
  )
}
