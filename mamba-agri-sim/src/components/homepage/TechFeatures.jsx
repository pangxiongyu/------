import { motion } from 'framer-motion';
import GlassCard from '../common/GlassCard';
import SectionTitle from '../common/SectionTitle';
import { techfeatures } from '../../data/statsData';
import { HiChip, HiCube, HiLightBulb, HiGlobe } from 'react-icons/hi';
const iconmap = {
  network: HiChip,
  algorithm: HiLightBulb,
  brain: HiGlobe,
  cube: HiCube
};
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
    y: 30
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: 'easeOut'
    }
  }
};
export default function TechFeatures() {
  return <section className="py-24 bg-gradient-to-b from-gray-50/80 via-white to-white relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-agri-50/40 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-blue-50/30 rounded-full blur-3xl translate-y-1/2 -translate-x-1/4 pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-6">
        <SectionTitle badge="核心技术" title="核心技术能力" subtitle="融合前沿 AI 算法与三维可视化技术，构建新一代智慧农业无人机控制平台" />

        <motion.div variants={container} initial="hidden" whileInView="visible" viewport={{
        once: true,
        margin: '-80px'
      }} className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {techfeatures.map((feature, idx) => {
          const Icon = iconmap[feature.icon];
          return <motion.div key={idx} variants={item}>
                <GlassCard variant="premium" className="text-center group h-full flex flex-col items-center">
                  {/* 顶部线 */}
                  <div className={`absolute top-0 left-4 right-4 h-[3px] rounded-b-full bg-gradient-to-r ${feature.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                  {/* 图标 */}
                  <div className={`relative w-16 h-16 mx-auto mb-5 rounded-2xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-110`}>
                    <Icon className="w-7 h-7 text-white" />
                    <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.gradient} blur-md opacity-0 group-hover:opacity-30 transition-opacity duration-300`} />
                  </div>

                  <h3 className="text-lg font-bold text-dark mb-3">{feature.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{feature.description}</p>
                </GlassCard>
              </motion.div>;
        })}
        </motion.div>
      </div>
    </section>;
}
