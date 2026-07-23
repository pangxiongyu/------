import { motion } from 'framer-motion';
import { summarycards } from '../../data/chartData';
import GlassCard from '../common/GlassCard';
import { HiTrendingUp, HiTrendingDown } from 'react-icons/hi';
const container = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.1
    }
  }
};
const item = {
  hidden: {
    opacity: 0,
    y: 16
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: 'easeOut'
    }
  }
};
export default function SummaryCards() {
  return <motion.div variants={container} initial="hidden" animate="visible" className="grid sm:grid-cols-3 gap-6 mb-8">
      {summarycards.map((card, idx) => <motion.div key={idx} variants={item}>
          <GlassCard variant="premium" className="relative overflow-hidden">
            {/* 顶部渐变条 */}
            <div className={`absolute top-0 left-4 right-4 h-[2px] rounded-full bg-gradient-to-r ${card.up ? 'from-agri-400 to-emerald-300' : 'from-red-400 to-rose-300'}`} />

            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-500 font-medium">{card.title}</span>
              <span className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${card.up ? 'text-agri-700 bg-agri-50' : 'text-red-600 bg-red-50'}`}>
                {card.up ? <HiTrendingUp className="w-3.5 h-3.5" /> : <HiTrendingDown className="w-3.5 h-3.5" />}
                {card.trend}
              </span>
            </div>

            <div className={`text-4xl font-black tracking-tight ${card.color}`}>
              {card.value}
            </div>

            {/* 趋势线占位 */}
            <div className="mt-3 flex items-end gap-[2px] h-8 opacity-30">
              {Array.from({
            length: 14
          }).map((unused, i) => <div key={i} className={`flex-1 rounded-sm ${card.up ? 'bg-agri-400' : 'bg-red-400'}`} style={{
            height: `${20 + Math.sin(i * 0.8) * 15 + Math.random() * 10}%`,
            opacity: 0.3 + i / 20
          }} />)}
            </div>
          </GlassCard>
        </motion.div>)}
    </motion.div>;
}
