import { HiBolt } from 'react-icons/hi2'
import { HiSignal, HiWifi } from 'react-icons/hi'

export default function UAVCard({ drone }) {
  const batteryColor = drone.battery > 80
    ? 'text-agri-500 bg-agri-50'
    : drone.battery > 50
    ? 'text-amber-500 bg-amber-50'
    : 'text-red-500 bg-red-50'

  const active = drone.status === 'active'

  return (
    <div className={`flex items-center gap-3 p-3.5 rounded-xl transition-all duration-300 cursor-default ${
      active
        ? 'bg-gradient-to-r from-agri-50/90 to-emerald-50/90 border border-agri-100/60 shadow-sm'
        : 'bg-gray-50/70 border border-transparent hover:bg-gray-50'
    }`}>
      {/* Drone icon */}
      <div className={`relative w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${
        active
          ? 'bg-gradient-to-br from-agri-500 to-emerald-600'
          : 'bg-gradient-to-br from-gray-400 to-gray-500'
      }`}>
        <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L2 19h6l4-8 4 8h6L12 2z"/>
          <circle cx="12" cy="19" r="1.5"/>
        </svg>
        {active && (
          <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-green-400 border-2 border-white animate-breathe" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-bold text-dark">{drone.id}</span>
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold tracking-wide ${
            active
              ? 'text-agri-700 bg-agri-100'
              : 'text-gray-400 bg-gray-100'
          }`}>
            {active ? '飞行中' : '待命'}
          </span>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-gray-400 mb-1.5 font-mono">
          <HiSignal className="w-3 h-3 text-gray-300" />
          <span>X:{drone.x.toFixed(1)}</span>
          <span>Y:{drone.y.toFixed(1)}</span>
          <span>Z:{drone.z.toFixed(1)}</span>
          {active && <HiWifi className="w-3 h-3 text-agri-400 ml-0.5" />}
        </div>

        {/* Battery bar */}
        <div className="flex items-center gap-1.5">
          <HiBolt className={`w-3.5 h-3.5 ${
            drone.battery > 80 ? 'text-agri-500' : drone.battery > 50 ? 'text-amber-500' : 'text-red-500'
          }`} />
          <div className="flex-1 h-1.5 bg-gray-200/80 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                drone.battery > 80
                  ? 'bg-gradient-to-r from-agri-400 to-emerald-500'
                  : drone.battery > 50
                  ? 'bg-gradient-to-r from-amber-400 to-orange-500'
                  : 'bg-gradient-to-r from-red-400 to-rose-500'
              }`}
              style={{ width: `${drone.battery}%` }}
            />
          </div>
          <span className={`text-[11px] font-bold tabular-nums ${
            drone.battery > 80 ? 'text-agri-600' : drone.battery > 50 ? 'text-amber-600' : 'text-red-500'
          }`}>{drone.battery}%</span>
        </div>
      </div>
    </div>
  )
}
