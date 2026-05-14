import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAppContext } from '../context/AppContext'
import PageContainer from '../components/common/PageContainer'
import GlassCard from '../components/common/GlassCard'
import SectionTitle from '../components/common/SectionTitle'
import { HiPaperAirplane, HiMap, HiCog, HiArrowRight } from 'react-icons/hi'

export default function FlightParamsPage() {
  const { flightParams, setFlightParams } = useAppContext()
  const navigate = useNavigate()
  const [local, setLocal] = useState({ ...flightParams })

  const update = (key, value) => setLocal((p) => ({ ...p, [key]: value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    setFlightParams(local)
    navigate('/viewport-3d')
  }

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto px-6 py-20">
        <SectionTitle
          badge="飞行配置"
          title="飞行参数设置"
          subtitle="配置无人机飞行航线参数与机载状态，一键启动智能路径规划"
        />

        <form onSubmit={handleSubmit}>
          <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Left - Coordinate form */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <GlassCard variant="premium" className="!p-7">
                <h2 className="text-xl font-bold text-dark mb-6 flex items-center gap-3">
                  <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center border border-blue-100/50">
                    <HiPaperAirplane className="w-5 h-5 text-blue-600" />
                  </span>
                  航线坐标设置
                </h2>

                {/* Mini coordinate visualization */}
                <div className="mb-6 p-4 rounded-xl bg-gray-50/80 border border-gray-100">
                  <svg viewBox="0 0 200 140" className="w-full h-32">
                    {/* Grid */}
                    {[0,1,2,3,4].map(i => (
                      <g key={i}>
                        <line x1={i*50} y1="0" x2={i*50} y2="140" stroke="#e5e7eb" strokeWidth="1"/>
                        <line x1="0" y1={i*35} x2="200" y2={i*35} stroke="#e5e7eb" strokeWidth="1"/>
                      </g>
                    ))}
                    {/* Axes */}
                    <line x1="10" y1="130" x2="190" y2="130" stroke="#059669" strokeWidth="1.5" markerEnd="url(#arrow)"/>
                    <line x1="10" y1="130" x2="10" y2="10" stroke="#059669" strokeWidth="1.5" markerEnd="url(#arrow)"/>
                    <defs>
                      <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                        <path d="M0 0L10 5L0 10Z" fill="#059669"/>
                      </marker>
                    </defs>
                    {/* Start point */}
                    <circle cx={10 + local.startX * 1.8} cy={130 - local.startY * 1.5} r="5" fill="#10B981" stroke="white" strokeWidth="2"/>
                    {/* End point */}
                    <circle cx={10 + local.endX * 1.8} cy={130 - local.endY * 1.5} r="5" fill="#2563EB" stroke="white" strokeWidth="2"/>
                    {/* Path line */}
                    <line
                      x1={10 + local.startX * 1.8} y1={130 - local.startY * 1.5}
                      x2={10 + local.endX * 1.8} y2={130 - local.endY * 1.5}
                      stroke="#10B981" strokeWidth="2" strokeDasharray="6,3" opacity="0.6"
                    />
                    {/* Labels */}
                    <text x="10" y="140" fill="#9CA3AF" fontSize="9">(0,0)</text>
                    <text x="10 + local.startX * 1.8" y="130 - local.startY * 1.5 - 8" fill="#059669" fontSize="9" textAnchor="middle">起点</text>
                    <text x="10 + local.endX * 1.8" y="130 - local.endY * 1.5 - 8" fill="#2563EB" fontSize="9" textAnchor="middle">终点</text>
                  </svg>
                  <div className="flex items-center gap-4 mt-2 justify-center text-xs text-gray-400">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-agri-500" />起点 ({local.startX}, {local.startY})</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" />终点 ({local.endX}, {local.endY})</span>
                  </div>
                </div>

                <div className="space-y-5">
                  <div className="grid grid-cols-2 gap-4">
                    <CoordInput label="起点 X" value={local.startX} onChange={(v) => update('startX', v)} />
                    <CoordInput label="起点 Y" value={local.startY} onChange={(v) => update('startY', v)} />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <CoordInput label="终点 X" value={local.endX} onChange={(v) => update('endX', v)} />
                    <CoordInput label="终点 Y" value={local.endY} onChange={(v) => update('endY', v)} />
                  </div>
                </div>

                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.97 }}
                  className="btn-primary w-full mt-8 flex items-center justify-center gap-2 text-lg py-4 shadow-glow-sm hover:shadow-glow bg-gradient-to-r from-agri-500 to-emerald-600 group"
                >
                  <HiPaperAirplane className="w-5 h-5" />
                  开始路径规划
                  <HiArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
                </motion.button>
              </GlassCard>
            </motion.div>

            {/* Right - Drone params */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <GlassCard variant="premium" className="!p-7">
                <h2 className="text-xl font-bold text-dark mb-6 flex items-center gap-3">
                  <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-agri-50 to-emerald-100 flex items-center justify-center border border-agri-100/50">
                    <HiCog className="w-5 h-5 text-agri-600" />
                  </span>
                  无人机与环境参数
                </h2>

                <div className="space-y-5">
                  <FormRow label="无人机编号">
                    <input
                      type="text" value={local.droneName}
                      onChange={(e) => update('droneName', e.target.value)}
                      className="input-glow"
                    />
                  </FormRow>

                  <div className="grid grid-cols-3 gap-3">
                    <FormRow label="X 坐标">
                      <input type="number" value={local.droneX}
                        onChange={(e) => update('droneX', Number(e.target.value))}
                        className="input-glow" />
                    </FormRow>
                    <FormRow label="Y 坐标">
                      <input type="number" value={local.droneY}
                        onChange={(e) => update('droneY', Number(e.target.value))}
                        className="input-glow" />
                    </FormRow>
                    <FormRow label="Z 坐标">
                      <input type="number" value={local.droneZ}
                        onChange={(e) => update('droneZ', Number(e.target.value))}
                        className="input-glow" />
                    </FormRow>
                  </div>

                  <FormRow label="电池电量">
                    <div className="flex items-center gap-4">
                      <div className="flex-1 relative">
                        <input
                          type="range" min="0" max="100" value={local.battery}
                          onChange={(e) => update('battery', Number(e.target.value))}
                          className="w-full h-2 rounded-full appearance-none cursor-pointer bg-gray-200
                            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6
                            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-gradient-to-br [&::-webkit-slider-thumb]:from-agri-500 [&::-webkit-slider-thumb]:to-emerald-600
                            [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white
                            [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-110"
                        />
                        <div
                          className="absolute top-0 left-0 h-2 rounded-full bg-gradient-to-r from-agri-400 to-emerald-500 pointer-events-none"
                          style={{ width: `${local.battery}%` }}
                        />
                      </div>
                      <span className={`text-lg font-black tabular-nums w-14 text-right ${
                        local.battery > 50 ? 'text-agri-600' : local.battery > 20 ? 'text-amber-500' : 'text-red-500'
                      }`}>
                        {local.battery}%
                      </span>
                    </div>
                  </FormRow>

                  <div className="space-y-3.5 pt-3">
                    {[
                      { key: 'speedCheck', label: '飞行速度自检', desc: '自动检测并优化飞行速度' },
                      { key: 'obstacleCheck', label: '障碍物检测开启', desc: '实时检测规避障碍物' },
                      { key: 'altitudeCheck', label: '高度自动调整', desc: '根据地形自适应高度' },
                    ].map((item) => (
                      <label
                        key={item.key}
                        className={`flex items-center gap-3.5 p-3 rounded-xl cursor-pointer transition-all duration-200 border ${
                          local[item.key]
                            ? 'bg-agri-50/70 border-agri-200/60'
                            : 'bg-gray-50/50 border-gray-100 hover:bg-gray-50'
                        }`}
                      >
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={local[item.key]}
                            onChange={(e) => update(item.key, e.target.checked)}
                            className="sr-only"
                          />
                          <div className={`w-11 h-6 rounded-full transition-colors duration-300 ${
                            local[item.key] ? 'bg-agri-500' : 'bg-gray-300'
                          }`}>
                            <div className={`w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-300 mt-0.5 ${
                              local[item.key] ? 'translate-x-5.5 ml-0.5' : 'translate-x-0.5'
                            }`} />
                          </div>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-800">{item.label}</span>
                          <p className="text-xs text-gray-400">{item.desc}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        </form>
      </div>
    </PageContainer>
  )
}

function CoordInput({ label, value, onChange }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-500 mb-1.5">{label}</label>
      <input
        type="number" value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="input-glow"
      />
    </div>
  )
}

function FormRow({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-500 mb-1.5">{label}</label>
      {children}
    </div>
  )
}
