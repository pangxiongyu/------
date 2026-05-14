import { DRONE_FLEET } from '../../data/droneFleet'
import UAVCard from './UAVCard'

export default function UAVControlPanel() {
  return (
    <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-white/40 p-6 h-full flex flex-col">
      <h2 className="text-xl font-black text-dark mb-1">三维无人机控制系统</h2>
      <p className="text-sm text-gray-400 mb-5">实时 UAV 状态监控 · 8 机编队</p>

      <div className="space-y-2 flex-1 overflow-y-auto">
        {DRONE_FLEET.map((drone) => (
          <UAVCard key={drone.id} drone={drone} />
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">编队状态</span>
          <span className="font-bold text-agri-500">
            {DRONE_FLEET.filter((d) => d.status === 'active').length} 飞行中
          </span>
        </div>
        <div className="flex items-center justify-between text-sm mt-1">
          <span className="text-gray-500">平均电量</span>
          <span className="font-bold text-dark">
            {Math.round(DRONE_FLEET.reduce((s, d) => s + d.battery, 0) / DRONE_FLEET.length)}%
          </span>
        </div>
      </div>
    </div>
  )
}
