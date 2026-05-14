import { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'
import GlassCard from '../common/GlassCard'
import SectionTitle from '../common/SectionTitle'
import { STATS } from '../../data/statsData'

function StatCard({ stat }) {
  const [count, setCount] = useState(0)
  const [inView, setInView] = useState(false)
  const ref = useRef(null)
  const Icon = stat.icon

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setInView(true) },
      { threshold: 0.3 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!inView) return
    const duration = 2000
    let startTime = null
    let frame
    const step = (ts) => {
      if (!startTime) startTime = ts
      const progress = Math.min((ts - startTime) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(eased * stat.value))
      if (progress < 1) frame = requestAnimationFrame(step)
    }
    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [inView, stat.value])

  return (
    <GlassCard ref={ref} variant="premium" className="stat-accent-bar pl-7">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-agri-50 to-emerald-100 flex items-center justify-center flex-shrink-0 border border-agri-100/50">
          <Icon className="w-6 h-6 text-agri-500" />
        </div>
        <div>
          <div className="flex items-baseline gap-1 mb-1">
            <span className="text-4xl font-black text-dark tabular-nums">{count}</span>
            <span className="text-2xl font-bold bg-gradient-to-r from-agri-500 to-emerald-600 bg-clip-text text-transparent">{stat.suffix}</span>
          </div>
          <div className="text-sm text-gray-500 font-medium">{stat.label}</div>
        </div>
      </div>
    </GlassCard>
  )
}

const container = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 },
  },
}

const itemAnim = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
}

export default function StatsGrid() {
  return (
    <section className="py-24 bg-white relative overflow-hidden">
      {/* Subtle background */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-agri-50/30 to-transparent rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-6">
        <SectionTitle
          badge="数据概览"
          title="系统运行统计"
          subtitle="覆盖全国主要农业产区，持续为智慧农业提供可靠数据支撑"
        />

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {STATS.map((stat, idx) => (
            <motion.div key={idx} variants={itemAnim}>
              <StatCard stat={stat} />
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
