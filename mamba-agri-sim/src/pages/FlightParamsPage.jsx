import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAppContext } from '../context/AppContext'
import PageContainer from '../components/common/PageContainer'
import GlassCard from '../components/common/GlassCard'
import SectionTitle from '../components/common/SectionTitle'
import SceneSelector from '../components/common/SceneSelector'
import {
  HiAdjustments,
  HiCheckCircle,
  HiCloud,
  HiCursorClick,
  HiLocationMarker,
  HiMap,
  HiMinus,
  HiPlus,
  HiRefresh,
} from 'react-icons/hi'

const WORKFLOW_STEPS = [
  {
    title: '选择无人机起点',
    text: '先在这里保存任务参数，进入三维控制后再在地形上放置绿色起飞点。',
  },
  {
    title: '设置任务目标点',
    text: '继续在三维控制页放置红色任务点，平原按果树行，梯田按分层田面。',
  },
  {
    title: '自动匹配航线',
    text: '三维控制页根据最近距离匹配任务并生成航线。',
  },
  {
    title: '能耗计算',
    text: '每架无人机按电量、基础耗电和风敏感系数计算消耗。',
  },
]

export default function FlightParamsPage() {
  const { flightParams, setFlightParams, selectedScene } = useAppContext()
  const [local, setLocal] = useState(() => ({
    droneCount: flightParams.droneCount ?? selectedScene.planning.droneCount,
    taskCount: flightParams.taskCount ?? selectedScene.planning.taskCount,
    autoAssignment: flightParams.autoAssignment ?? true,
  }))

  const focusLayer = selectedScene.windLayers.find((layer) => layer.id === selectedScene.focusLayerId) ?? selectedScene.windLayers[0]

  const update = (key, value) => setLocal((current) => ({ ...current, [key]: value }))

  const handleSubmit = (event) => {
    event.preventDefault()
    setFlightParams({
      droneCount: local.droneCount,
      taskCount: local.taskCount,
      autoAssignment: local.autoAssignment,
      sceneId: selectedScene.id,
      windLayers: selectedScene.windLayers,
    })
  }

  return (
    <PageContainer className="bg-gradient-to-b from-slate-950 via-emerald-950 to-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-14 md:py-18">
        <SectionTitle
          badge="飞行任务配置"
          title="先配置参数，再从导航进入三维控制"
          subtitle="这里用于选择场景、确认风场、设置起点和任务点数量；三维页面只保留顶部导航中的「三维控制」一个入口。"
          light
        />

        <SceneSelector className="mb-8" />

        <form onSubmit={handleSubmit}>
          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <motion.aside
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45 }}
              className="space-y-5"
            >
              <GlassCard variant="premium" hover={false} className="!rounded-lg !p-6">
                <div className="flex items-start gap-4">
                  <span className="text-5xl leading-none">{selectedScene.icon}</span>
                  <div>
                    <p className="text-sm font-bold text-agri-600">{selectedScene.badge}</p>
                    <h2 className="mt-1 text-2xl font-black text-dark">{selectedScene.name}</h2>
                    <p className="mt-3 text-sm leading-relaxed text-slate-500">{selectedScene.summary}</p>
                  </div>
                </div>

                <div className="mt-6 grid gap-3 text-sm">
                  <SceneFact icon={<HiLocationMarker />} label="起降策略" value={selectedScene.params.start} />
                  <SceneFact icon={<HiMap />} label="任务类型" value={selectedScene.params.task} />
                  <SceneFact icon={<HiRefresh />} label="路径策略" value={selectedScene.params.route} />
                  <SceneFact icon={<HiCloud />} label="重点风层" value={`${focusLayer.label} ${focusLayer.height}m`} />
                </div>
              </GlassCard>

              <GlassCard variant="premium" hover={false} className="!rounded-lg !p-6">
                <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-dark">
                  <HiCursorClick className="h-5 w-5 text-agri-600" />
                  进入三维后的作业流程
                </h3>
                <div className="space-y-3">
                  {WORKFLOW_STEPS.map((step, index) => (
                    <WorkflowStep key={step.title} index={index + 1} title={step.title} text={step.text} />
                  ))}
                </div>
              </GlassCard>
            </motion.aside>

            <motion.section
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.08 }}
              className="grid gap-6 xl:grid-cols-2"
            >
              <GlassCard variant="premium" hover={false} className="!rounded-lg !p-6">
                <h2 className="mb-5 flex items-center gap-3 text-xl font-black text-dark">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-agri-50 text-agri-600">
                    <HiAdjustments className="h-5 w-5" />
                  </span>
                  航线配置中心
                </h2>

                <div className="space-y-5">
                  <CounterControl
                    label="无人机起点"
                    value={local.droneCount}
                    min={1}
                    max={12}
                    onChange={(value) => update('droneCount', value)}
                    description="对应三维控制页中的绿色起飞点数量"
                  />
                  <CounterControl
                    label="任务目标点"
                    value={local.taskCount}
                    min={1}
                    max={20}
                    onChange={(value) => update('taskCount', value)}
                    description="对应三维控制页中的红色任务点数量"
                  />

                  <label className="flex cursor-pointer items-center justify-between gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                    <span>
                      <span className="block text-sm font-black text-slate-800">自动匹配航线</span>
                      <span className="mt-1 block text-xs leading-relaxed text-slate-500">{selectedScene.planning.assignment}</span>
                    </span>
                    <input
                      type="checkbox"
                      checked={local.autoAssignment}
                      onChange={(event) => update('autoAssignment', event.target.checked)}
                      className="h-5 w-5 shrink-0 accent-emerald-500"
                    />
                  </label>

                  <div className="rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm leading-relaxed text-emerald-800">
                    <strong>布点提示：</strong>{selectedScene.planning.placement}
                  </div>
                </div>
              </GlassCard>

              <GlassCard variant="premium" hover={false} className="!rounded-lg !p-6">
                <h2 className="mb-5 flex items-center gap-3 text-xl font-black text-dark">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-50 text-sky-600">
                    <HiCloud className="h-5 w-5" />
                  </span>
                  风场高度层
                </h2>

                <div className="space-y-3">
                  {selectedScene.windLayers.map((layer) => (
                    <WindLayerRow key={layer.id} layer={layer} active={layer.id === selectedScene.focusLayerId} />
                  ))}
                </div>
              </GlassCard>

              <GlassCard variant="premium" hover={false} className="!rounded-lg !p-6 xl:col-span-2">
                <div className="flex flex-col justify-between rounded-lg border border-slate-100 bg-slate-50 p-5">
                  <div>
                    <p className="text-sm font-black text-slate-800">保存后从顶部导航进入三维控制</p>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                      当前页面只保存飞行参数，不再自动跳转到三维页面，避免多个入口造成状态混乱。
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <StatusBadge>场景已选择</StatusBadge>
                      <StatusBadge>风场已加载</StatusBadge>
                      <StatusBadge>布点在三维页完成</StatusBadge>
                    </div>
                  </div>

                  <motion.button
                    type="submit"
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.98 }}
                    className="btn-primary mt-6 flex w-full items-center justify-center gap-2 rounded-lg py-4 text-base shadow-glow-sm sm:text-lg"
                  >
                    保存 {selectedScene.shortName} 飞行配置
                    <HiCheckCircle className="h-5 w-5" />
                  </motion.button>
                </div>
              </GlassCard>
            </motion.section>
          </div>
        </form>
      </div>
    </PageContainer>
  )
}

function SceneFact({ icon, label, value }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
      <span className="flex min-w-0 items-center gap-2 font-semibold text-slate-500">
        <span className="text-agri-600">{icon}</span>
        {label}
      </span>
      <span className="text-right font-bold text-slate-800">{value}</span>
    </div>
  )
}

function WorkflowStep({ index, title, text }) {
  return (
    <div className="flex gap-3 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-agri-500 text-sm font-black text-white">
        {index}
      </span>
      <span>
        <span className="block text-sm font-black text-slate-800">{title}</span>
        <span className="mt-1 block text-xs leading-relaxed text-slate-500">{text}</span>
      </span>
    </div>
  )
}

function CounterControl({ label, value, min, max, onChange, description }) {
  const setClampedValue = (nextValue) => {
    onChange(Math.min(max, Math.max(min, nextValue)))
  }

  return (
    <div className="rounded-lg border border-slate-100 bg-white px-4 py-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-black text-slate-800">{label}</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">{description}</p>
        </div>
        <div className="flex h-10 shrink-0 items-center overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
          <button
            type="button"
            onClick={() => setClampedValue(value - 1)}
            className="flex h-10 w-10 items-center justify-center text-slate-500 transition-colors hover:bg-white hover:text-agri-600"
            aria-label={`减少${label}`}
          >
            <HiMinus className="h-4 w-4" />
          </button>
          <input
            type="number"
            min={min}
            max={max}
            value={value}
            onChange={(event) => setClampedValue(Number(event.target.value))}
            className="h-10 w-14 border-x border-slate-200 bg-white text-center text-base font-black text-slate-900 outline-none"
          />
          <button
            type="button"
            onClick={() => setClampedValue(value + 1)}
            className="flex h-10 w-10 items-center justify-center text-slate-500 transition-colors hover:bg-white hover:text-agri-600"
            aria-label={`增加${label}`}
          >
            <HiPlus className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

function WindLayerRow({ layer, active }) {
  return (
    <div className={`rounded-lg border px-4 py-3 ${active ? 'border-agri-200 bg-agri-50' : 'border-slate-100 bg-white'}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: layer.color }} />
          <span>
            <span className="block text-sm font-black text-slate-800">{layer.label}</span>
            <span className="text-xs text-slate-500">{layer.note}</span>
          </span>
        </div>
        {active && (
          <span className="inline-flex items-center gap-1 rounded-full bg-agri-500 px-2.5 py-1 text-xs font-bold text-white">
            <HiCheckCircle className="h-3.5 w-3.5" />
            当前重点
          </span>
        )}
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
        <LayerMetric label="高度" value={`${layer.height}m`} />
        <LayerMetric label="风速" value={`${layer.speed}m/s`} />
        <LayerMetric label="方向" value={`${layer.direction}°`} />
      </div>
    </div>
  )
}

function LayerMetric({ label, value }) {
  return (
    <div className="rounded-md bg-white/80 px-2 py-2">
      <span className="block text-slate-400">{label}</span>
      <span className="mt-0.5 block font-black text-slate-800">{value}</span>
    </div>
  )
}

function StatusBadge({ children }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-xs font-bold text-agri-700">
      <HiCheckCircle className="h-3.5 w-3.5" />
      {children}
    </span>
  )
}
