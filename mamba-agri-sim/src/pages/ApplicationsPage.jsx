import { motion, AnimatePresence } from 'framer-motion';
import { useappcontext } from '../context/AppContext';
import { agricultureapps } from '../data/agricultureApps';
import PageContainer from '../components/common/PageContainer';
import GlassCard from '../components/common/GlassCard';
import SectionTitle from '../components/common/SectionTitle';
import { HiCheck, HiArrowRight } from 'react-icons/hi';
export default function ApplicationsPage() {
  const {
    selectedApp: selectedapp,
    setSelectedApp: setselectedapp
  } = useappcontext();
  const app = agricultureapps[selectedapp];
  return <PageContainer>
      <div className="max-w-7xl mx-auto px-6 py-20">
        <SectionTitle badge="应用矩阵" title="智慧农业应用" subtitle="基于无人机遥感与 AI 分析的全方位智慧农业应用矩阵" />

        <div className="grid lg:grid-cols-[300px_1fr] gap-8">
          {/* 左侧栏 */}
          <div className="space-y-1.5">
            {agricultureapps.map(item => {
            const active = selectedapp === item.id;
            return <motion.button key={item.id} onClick={() => setselectedapp(item.id)} whileHover={{
              x: 4
            }} whileTap={{
              scale: 0.98
            }} className={`w-full text-left px-5 py-3.5 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-3 group ${active ? 'bg-gradient-to-r from-agri-500 to-emerald-600 text-white shadow-lg shadow-agri-200/50' : 'text-gray-600 hover:bg-gray-50 hover:text-agri-600'}`}>
                  <span className={`text-xl transition-transform duration-300 ${active ? 'scale-110' : 'group-hover:scale-110'}`}>
                    {item.icon}
                  </span>
                  <span className="flex-1">{item.name}</span>
                  {active && <HiArrowRight className="w-4 h-4 opacity-70" />}
                </motion.button>;
          })}
          </div>

          {/* 右侧详情 */}
          <AnimatePresence mode="wait">
            <motion.div key={app.id} initial={{
            opacity: 0,
            y: 20
          }} animate={{
            opacity: 1,
            y: 0
          }} exit={{
            opacity: 0,
            y: -10
          }} transition={{
            duration: 0.3
          }}>
              <GlassCard variant="premium" className="!p-0 overflow-hidden">
                {/* 横幅 */}
                <div className="relative aspect-[21/9] bg-gradient-to-br from-agri-600 via-emerald-700 to-teal-800 flex items-center justify-center overflow-hidden">
                  {/* 背景遮罩 */}
                  <div className="absolute inset-0 bg-cover bg-center opacity-25" style={{
                  backgroundImage: `url(${app.image})`
                }} />
                  {/* 装饰元素 */}
                  <div className="absolute top-6 right-6 w-32 h-32 bg-white/5 rounded-full blur-2xl" />
                  <div className="absolute bottom-4 left-8 w-24 h-24 bg-agri-300/10 rounded-full blur-xl" />

                  <div className="relative z-10 text-center p-8">
                    <motion.span initial={{
                    scale: 0
                  }} animate={{
                    scale: 1
                  }} transition={{
                    type: 'spring',
                    stiffness: 200,
                    damping: 15
                  }} className="text-6xl mb-5 block drop-shadow-lg">
                      {app.icon}
                    </motion.span>
                    <h2 className="text-3xl font-black text-white drop-shadow-md">{app.name}</h2>
                  </div>

                  {/* 底部渐变 */}
                  <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white/5 to-transparent" />
                </div>

                {/* 内容 */}
                <div className="p-8">
                  <p className="text-gray-600 leading-relaxed mb-8 text-base">{app.description}</p>

                  <h3 className="text-lg font-bold text-dark mb-5 flex items-center gap-2">
                    <span className="w-1 h-5 rounded-full bg-gradient-to-b from-agri-400 to-agri-600" />
                    核心功能
                  </h3>

                  <div className="grid sm:grid-cols-2 gap-3">
                    {app.features.map((feat, idx) => <div key={idx} className="flex items-start gap-3 bg-agri-50/70 rounded-xl p-4 border border-agri-100/50 hover:border-agri-200 hover:bg-agri-50 transition-all duration-200 cursor-default">
                        <div className="w-6 h-6 rounded-full bg-agri-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <HiCheck className="w-3.5 h-3.5 text-agri-600" />
                        </div>
                        <span className="text-sm text-gray-700 leading-snug">{feat}</span>
                      </div>)}
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </PageContainer>;
}
