import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import PageContainer from '../components/common/PageContainer'
import GlassCard from '../components/common/GlassCard'
import SectionTitle from '../components/common/SectionTitle'
import { HiArrowRight, HiCheck, HiMap, HiShieldCheck, HiLightningBolt, HiChip } from 'react-icons/hi'

const features = [
  { icon: HiMap, title: '全自主规划', desc: '无人机全自主路径规划，适应复杂山地起伏' },
  { icon: HiShieldCheck, title: '智能避障', desc: '实时动态障碍物检测与智能规避' },
  { icon: HiChip, title: '精准喷洒', desc: '厘米级精准喷洒作业，减少农药浪费' },
  { icon: HiLightningBolt, title: '多机协同', desc: '多机协同覆盖，作业效率提升 300%' },
]

export default function SceneDetailPage() {
  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto px-6 py-20">
        <SectionTitle
          badge="场景详情"
          title="桃园山地场景"
          subtitle="复杂地形智能飞行解决方案，专为丘陵山地果园打造"
        />

        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left - illustration */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="relative"
          >
            <div className="aspect-[4/3] rounded-3xl overflow-hidden shadow-2xl shadow-agri-200/30 ring-1 ring-agri-100/50">
              <div className="w-full h-full bg-gradient-to-br from-rose-100 via-green-50 to-emerald-100 flex items-center justify-center relative overflow-hidden">
                <svg className="w-full h-full absolute inset-0" viewBox="0 0 400 300">
                  {/* Sky gradient */}
                  <defs>
                    <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#7DD3FC"/>
                      <stop offset="60%" stopColor="#BAE6FD"/>
                      <stop offset="100%" stopColor="#E0F2FE"/>
                    </linearGradient>
                    <linearGradient id="mountainGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#78716C"/>
                      <stop offset="100%" stopColor="#A8A29E"/>
                    </linearGradient>
                    <radialGradient id="sunGlow" cx="80%" cy="15%" r="30%">
                      <stop offset="0%" stopColor="#FEF08A" stopOpacity="0.6"/>
                      <stop offset="100%" stopColor="#FEF08A" stopOpacity="0"/>
                    </radialGradient>
                  </defs>

                  {/* Sky */}
                  <rect width="400" height="300" fill="url(#skyGrad)"/>
                  <circle cx="320" cy="45" r="80" fill="url(#sunGlow)"/>

                  {/* Clouds */}
                  <g className="animate-cloud-drift" opacity="0.6">
                    <ellipse cx="80" cy="50" rx="35" ry="10" fill="white"/>
                    <ellipse cx="95" cy="45" rx="25" ry="12" fill="white"/>
                    <ellipse cx="65" cy="47" rx="18" ry="8" fill="white"/>
                  </g>
                  <g className="animate-cloud-drift" opacity="0.4" style={{ animationDelay: '-4s' }}>
                    <ellipse cx="280" cy="35" rx="28" ry="8" fill="white"/>
                    <ellipse cx="295" cy="32" rx="20" ry="9" fill="white"/>
                  </g>

                  {/* Mountains */}
                  <polygon points="0,180 90,80 180,180" fill="url(#mountainGrad)" opacity="0.7"/>
                  <polygon points="120,180 250,55 380,180" fill="url(#mountainGrad)" opacity="0.85"/>
                  <polygon points="280,180 370,90 400,180" fill="url(#mountainGrad)" opacity="0.5"/>

                  {/* Hills */}
                  <ellipse cx="200" cy="200" rx="230" ry="85" fill="#86EFAC" opacity="0.45"/>
                  <ellipse cx="100" cy="230" rx="160" ry="65" fill="#4ADE80" opacity="0.5"/>
                  <ellipse cx="330" cy="240" rx="130" ry="55" fill="#22C55E" opacity="0.35"/>

                  {/* Orchard rows - peach trees */}
                  {[0,1,2,3,4].map(i => (
                    <g key={i}>
                      {[0,1,2,3,4,5].map(j => (
                        <g key={j}>
                          <circle cx={58 + j*62 + i*12} cy={172 + i*26} r="14" fill="#FB7185" opacity="0.65"/>
                          <circle cx={58 + j*62 + i*12} cy={168 + i*26} r="5" fill="#FDA4AF" opacity="0.5"/>
                        </g>
                      ))}
                    </g>
                  ))}

                  {/* Dirt path */}
                  <path d="M0 285 Q100 225 200 245 Q300 265 400 235" stroke="#A16207" strokeWidth="3.5" fill="none" opacity="0.4" strokeDasharray="10,5"/>

                  {/* Drone */}
                  <g className="animate-drone-hover" transform="translate(250, 125)">
                    <ellipse cx="0" cy="0" rx="16" ry="6" fill="#1F2937" opacity="0.75"/>
                    <line x1="-14" y1="0" x2="14" y2="0" stroke="#374151" strokeWidth="1.8"/>
                    <line x1="0" y1="-14" x2="0" y2="14" stroke="#374151" strokeWidth="1.8"/>
                    <circle cx="-14" cy="0" r="5" fill="none" stroke="#3B82F6" strokeWidth="0.8" opacity="0.5"/>
                    <circle cx="14" cy="0" r="5" fill="none" stroke="#3B82F6" strokeWidth="0.8" opacity="0.5"/>
                    <circle cx="0" cy="-14" r="5" fill="none" stroke="#3B82F6" strokeWidth="0.8" opacity="0.5"/>
                    <circle cx="0" cy="14" r="5" fill="none" stroke="#3B82F6" strokeWidth="0.8" opacity="0.5"/>
                    <circle cx="0" cy="-8" r="7" fill="#3B82F6" opacity="0.3"/>
                  </g>

                  {/* Spray effect */}
                  <g opacity="0.25">
                    {[0,1,2,3,4,5].map(k => (
                      <circle key={k} cx={240 + k*5} cy={145 + k*3} r={1.5} fill="#3B82F6" opacity={0.5 - k*0.07}/>
                    ))}
                  </g>
                </svg>
              </div>
            </div>

            {/* Overlay badge */}
            <div className="absolute -bottom-3 left-6 right-6">
              <GlassCard className="!p-3 !rounded-xl text-center shadow-lg">
                <span className="text-sm font-bold text-agri-700 flex items-center justify-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-agri-500 animate-pulse" />
                  桃园 · 丘陵山地地形 · 135 亩
                </span>
              </GlassCard>
            </div>
          </motion.div>

          {/* Right - feature cards */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut', delay: 0.15 }}
          >
            <p className="text-gray-600 text-lg leading-relaxed mb-8">
              桃园山地位于丘陵起伏地带，地形复杂多变，传统人工喷洒效率低、覆盖不均匀。
              本系统针对山地果园特殊需求，提供全自主路径规划与动态避障能力。
            </p>

            <div className="grid sm:grid-cols-2 gap-4 mb-8">
              {features.map((feat, idx) => (
                <GlassCard key={idx} variant="premium" className="!p-5 group cursor-default">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-agri-50 to-emerald-100 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-300 border border-agri-100/50">
                    <feat.icon className="w-5 h-5 text-agri-500" />
                  </div>
                  <h4 className="font-bold text-dark text-sm mb-1">{feat.title}</h4>
                  <p className="text-xs text-gray-500 leading-relaxed">{feat.desc}</p>
                </GlassCard>
              ))}
            </div>

            <Link to="/flight-params" className="btn-primary bg-agri-500 hover:bg-agri-600 text-lg px-8 py-4 inline-flex items-center gap-2 group shadow-glow-sm hover:shadow-glow">
              进入场景
              <HiArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
            </Link>
          </motion.div>
        </div>
      </div>
    </PageContainer>
  )
}
