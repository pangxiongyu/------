import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import PageContainer from '../components/common/PageContainer';
import GlassCard from '../components/common/GlassCard';
import SectionTitle from '../components/common/SectionTitle';
import SceneSelector from '../components/common/SceneSelector';
import { useappcontext } from '../context/AppContext';
import { HiChartBar, HiCog, HiCube, HiLocationMarker } from 'react-icons/hi';
export default function SceneDetailPage() {
  const {
    selectedScene: selectedscene
  } = useappcontext();
  const metricrows = [['地形结构', selectedscene.terrain], ['作物类型', selectedscene.crop], ['作业高程', selectedscene.altitude], ['风场配置', selectedscene.wind]];
  return <PageContainer className="bg-gradient-to-b from-slate-950 via-emerald-950 to-slate-50">
      <div className="max-w-7xl mx-auto px-6 py-14 md:py-18">
        <SectionTitle badge="场景详情" title="双场景作业空间" subtitle="在这里选择和查看作业场景；三维控制只从顶部导航进入，避免多个入口造成状态混乱。" light />

        <SceneSelector className="mb-8" />

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <motion.section initial={{
          opacity: 0,
          y: 18
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          duration: 0.45
        }} className="overflow-hidden rounded-lg border border-white/12 bg-white/[0.08] shadow-2xl shadow-black/20 backdrop-blur-xl">
            <div className="relative min-h-[420px] overflow-hidden">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_22%_18%,rgba(16,185,129,0.30),transparent_28%),linear-gradient(135deg,#092016_0%,#113323_45%,#153450_100%)]" />
              <div className="absolute inset-x-0 bottom-0 h-56 bg-gradient-to-t from-black/45 to-transparent" />
              <div className="absolute inset-0 opacity-35">
                <SceneTopography sceneId={selectedscene.id} />
              </div>
              <div className="relative z-10 flex min-h-[420px] flex-col justify-end p-6 md:p-8">
                <div className="mb-4 inline-flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/12 px-3 py-1.5 text-sm font-semibold text-white backdrop-blur">
                  <HiCube className="h-4 w-4 text-agri-300" />
                  {selectedscene.badge}
                </div>
                <h3 className="text-3xl font-black text-white md:text-5xl">
                  {selectedscene.icon} {selectedscene.name}
                </h3>
                <p className="mt-4 max-w-2xl text-base leading-relaxed text-white/78">
                  {selectedscene.summary}
                </p>
              </div>
            </div>
          </motion.section>

          <motion.aside initial={{
          opacity: 0,
          y: 18
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          duration: 0.45,
          delay: 0.08
        }} className="space-y-5">
            <GlassCard variant="premium" hover={false} className="!rounded-lg !p-6">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-agri-50 text-agri-600">
                  <HiLocationMarker className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="text-xl font-black text-dark">{selectedscene.shortName}参数面板</h3>
                  <p className="text-sm text-slate-500">{selectedscene.acreage} · {selectedscene.params.risk}风险</p>
                </div>
              </div>

              <div className="mt-6 grid gap-3">
                {metricrows.map(([label, value]) => <div key={label} className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                    <span className="text-sm font-semibold text-slate-500">{label}</span>
                    <span className="text-right text-sm font-bold text-slate-800">{value}</span>
                  </div>)}
              </div>
            </GlassCard>

            <GlassCard variant="premium" hover={false} className="!rounded-lg !p-6">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-black text-dark">
                <HiChartBar className="h-5 w-5 text-agri-600" />
                作业特征
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {selectedscene.highlights.map(item => <span key={item} className="rounded-lg bg-agri-50 px-3 py-3 text-sm font-bold text-agri-800">
                    {item}
                  </span>)}
              </div>
            </GlassCard>

            <div className="grid gap-3">
              <Link to="/flight-params" className="btn-primary justify-center rounded-lg py-3">
                <HiCog className="h-5 w-5" />
                配置飞行参数
              </Link>
              <p className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 text-center text-sm font-semibold text-slate-500">
                三维控制统一从顶部导航进入
              </p>
            </div>
          </motion.aside>
        </div>
      </div>
    </PageContainer>;
}
function SceneTopography({
  sceneId: sceneid
}) {
  const rows = sceneid === 'modern' ? ['M60 260 L340 80', 'M20 160 L380 160', 'M90 310 L360 120', 'M30 230 L330 55'] : ['M0 290 C70 250 130 265 200 220 C270 175 320 195 400 130', 'M0 235 C80 215 135 225 205 185 C270 150 330 160 400 115', 'M0 180 C70 165 130 175 205 140 C280 100 340 115 400 75'];
  return <svg viewBox="0 0 400 320" className="h-full w-full" preserveAspectRatio="none">
      <rect width="400" height="320" fill="rgba(5,150,105,0.18)" />
      {rows.map((d, index) => <path key={d} d={d} fill="none" stroke={index % 2 ? '#a7f3d0' : '#facc15'} strokeWidth="8" strokeLinecap="round" opacity="0.55" />)}
      {Array.from({
      length: 46
    }).map((unused, index) => {
      const x = 24 + index % 10 * 38 + (sceneid === 'modern' ? 0 : index % 3 * 8);
      const y = 58 + Math.floor(index / 10) * 48 + (sceneid === 'modern' ? 0 : index % 4 * 10);
      return <circle key={index} cx={x} cy={y} r="5" fill="#34d399" opacity="0.72" />;
    })}
    </svg>;
}
