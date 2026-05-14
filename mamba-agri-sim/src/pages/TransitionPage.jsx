import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import PageContainer from '../components/common/PageContainer'
import { HiArrowRight, HiStar } from 'react-icons/hi'

export default function TransitionPage() {
  return (
    <PageContainer>
      <div className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-sky-50 via-blue-50 to-indigo-50 flex items-center justify-center relative overflow-hidden">
        {/* Floating decorations */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
          className="absolute top-16 left-16 w-24 h-24 border-2 border-blue-200/40 rounded-full"
        />
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
          className="absolute bottom-24 right-20 w-20 h-20 border-2 border-indigo-200/30 rounded-2xl rotate-45"
        />
        <div className="absolute top-1/4 right-1/4 w-3 h-3 bg-blue-300/40 rounded-full animate-float" />
        <div className="absolute bottom-1/3 left-1/4 w-2 h-2 bg-indigo-300/40 rounded-full animate-float" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/3 left-1/3 w-4 h-4 bg-blue-200/30 rounded-lg rotate-12 animate-float" style={{ animationDelay: '1.8s' }} />

        {/* Center frame */}
        <motion.div
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="relative"
        >
          {/* Outer decoration rings */}
          <div className="absolute -inset-10 border-2 border-blue-200/25 rounded-3xl animate-pulse" style={{ animationDuration: '4s' }} />
          <div className="absolute -inset-6 border border-blue-200/15 rounded-2xl rotate-2" />

          {/* Main card */}
          <div className="relative bg-white/65 backdrop-blur-xl rounded-3xl border border-white/60 shadow-2xl shadow-blue-200/20 px-16 py-14 text-center">
            {/* Corner decorations */}
            <DecoCorner className="top-4 left-4" />
            <DecoCorner className="top-4 right-4 rotate-90" />
            <DecoCorner className="bottom-4 right-4 rotate-180" />
            <DecoCorner className="bottom-4 left-4 -rotate-90" />

            <motion.div
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              <div className="relative inline-block mb-4">
                <span className="text-8xl font-black bg-gradient-to-br from-agri-400 to-emerald-600 bg-clip-text text-transparent">
                  06
                </span>
                <HiStar className="absolute -top-2 -right-6 w-8 h-8 text-amber-400 animate-pulse" />
              </div>
            </motion.div>

            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.5 }}
            >
              <h2 className="text-2xl font-bold text-dark mb-3">核心功能模块</h2>
              <p className="text-gray-500 text-sm max-w-xs mx-auto mb-8 leading-relaxed">
                GAT + Mamba-MPSO · 三维地形可视化 · 智能农业应用矩阵
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="flex flex-col items-center gap-3"
            >
              <Link
                to="/data-display"
                className="btn-primary bg-gradient-to-r from-agri-500 to-emerald-600 inline-flex items-center gap-2 shadow-glow-sm hover:shadow-glow group"
              >
                进入功能
                <HiArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
              </Link>
              <Link to="/" className="text-sm text-gray-400 hover:text-agri-500 transition-colors">
                返回首页
              </Link>
            </motion.div>
          </div>
        </motion.div>

        {/* Bottom branding */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2.5 bg-white/70 backdrop-blur-sm rounded-full px-5 py-2.5 border border-white/50 shadow-sm">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-agri-500 to-agri-700 flex items-center justify-center shadow-sm">
            <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 19h6l4-8 4 8h6L12 2z"/>
              <circle cx="12" cy="19" r="2"/>
            </svg>
          </div>
          <span className="text-sm font-bold text-dark">Mamba<span className="text-agri-500">AgriSim</span></span>
        </div>
      </div>
    </PageContainer>
  )
}

function DecoCorner({ className }) {
  return (
    <svg className={`absolute w-6 h-6 text-blue-300/30 ${className}`} viewBox="0 0 20 20" fill="none">
      <path d="M0 10 L0 0 L10 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  )
}
