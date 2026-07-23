import { motion } from 'framer-motion';
import PageContainer from '../components/common/PageContainer';
import { HiStar } from 'react-icons/hi';
export default function ThanksPage() {
  return <PageContainer>
      <div className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-emerald-900 via-teal-800 to-cyan-900 flex items-center justify-center relative overflow-hidden">
        {/* 山形剪影 */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 200" preserveAspectRatio="none" className="w-full h-auto">
            <polygon points="0,200 0,80 200,30 400,100 600,20 800,80 1000,10 1200,60 1440,20 1440,200" fill="rgba(0,0,0,0.15)" />
            <polygon points="0,200 0,120 150,80 300,140 500,60 700,120 900,50 1100,100 1300,40 1440,90 1440,200" fill="rgba(0,0,0,0.1)" />
          </svg>
        </div>

        {/* 星光粒子 */}
        {Array.from({
        length: 30
      }).map((unused, i) => <div key={i} className="absolute rounded-full animate-pulse" style={{
        width: `${2 + Math.random() * 3}px`,
        height: `${2 + Math.random() * 3}px`,
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 60}%`,
        backgroundColor: `rgba(255,255,255,${0.2 + Math.random() * 0.4})`,
        animationDelay: `${Math.random() * 3}s`,
        animationDuration: `${2 + Math.random() * 3}s`
      }} />)}

        {/* 发光圆形 */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-gold/5 rounded-full blur-3xl animate-breathe" />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-amber-400/5 rounded-full blur-3xl animate-breathe" style={{
        animationDelay: '1.5s'
      }} />

        <div className="relative z-10 text-center px-6">
          <motion.div initial={{
          scale: 0.5,
          opacity: 0
        }} animate={{
          scale: 1,
          opacity: 1
        }} transition={{
          duration: 0.8,
          ease: 'easeOut'
        }}>
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-black mb-6 tracking-wider">
              <span className="bg-gradient-to-r from-gold via-amber-300 to-yellow-400 bg-clip-text text-transparent animate-breathe">
                THANKS FOR WATCHING
              </span>
            </h1>
          </motion.div>

          <motion.div initial={{
          y: 30,
          opacity: 0
        }} animate={{
          y: 0,
          opacity: 1
        }} transition={{
          delay: 0.5,
          duration: 0.6
        }}>
            <p className="text-3xl md:text-4xl font-bold text-white/90 mb-4">感谢观看</p>
          </motion.div>

          <motion.div initial={{
          opacity: 0
        }} animate={{
          opacity: 1
        }} transition={{
          delay: 1
        }} className="mt-8">
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-white/10 backdrop-blur-sm rounded-full border border-white/15 shadow-lg">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-gold to-amber-600 flex items-center justify-center shadow-md">
                <HiStar className="w-4 h-4 text-white" />
              </div>
              <span className="text-white/85 font-bold text-lg">智翼农航</span>
            </div>
          </motion.div>

          <motion.p initial={{
          opacity: 0
        }} animate={{
          opacity: 1
        }} transition={{
          delay: 1.3
        }} className="text-white/30 text-sm mt-8 tracking-widest">
            智慧农业无人机协同系统
          </motion.p>
        </div>

        {/* 边角装饰 */}
        <div className="absolute top-8 left-8 w-14 h-14 border-t border-l border-white/15 rounded-tl-2xl" />
        <div className="absolute top-8 right-8 w-14 h-14 border-t border-r border-white/15 rounded-tr-2xl" />
        <div className="absolute bottom-8 left-8 w-14 h-14 border-b border-l border-white/15 rounded-bl-2xl" />
        <div className="absolute bottom-8 right-8 w-14 h-14 border-b border-r border-white/15 rounded-br-2xl" />
      </div>
    </PageContainer>;
}
