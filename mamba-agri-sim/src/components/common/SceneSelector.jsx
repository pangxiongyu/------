import { useAppContext } from '../../context/AppContext'

export default function SceneSelector({
  className = '',
  compact = false,
  onSelect,
}) {
  const { scenes, selectedSceneId, setSelectedSceneId } = useAppContext()

  const handleSelect = (sceneId) => {
    setSelectedSceneId(sceneId)
    onSelect?.(sceneId)
  }

  return (
    <div className={`${compact ? 'grid grid-cols-2 gap-2' : 'grid gap-4 md:grid-cols-2'} ${className}`}>
      {scenes.map((scene) => {
        const active = scene.id === selectedSceneId
        return (
          <button
            key={scene.id}
            type="button"
            aria-pressed={active}
            onClick={() => handleSelect(scene.id)}
            className={`group relative overflow-hidden rounded-lg border text-left transition-all duration-300 ${
              compact ? 'p-3' : 'p-5'
            } ${
              active
                ? 'border-agri-400 bg-agri-50 shadow-glow-sm'
                : 'border-slate-200 bg-white/80 hover:border-agri-200 hover:bg-white hover:shadow-card'
            }`}
          >
            <span className={`absolute inset-y-0 left-0 w-1 ${active ? 'bg-agri-500' : 'bg-slate-200 group-hover:bg-agri-300'}`} />
            <div className="flex items-start gap-3">
              <span className={`${compact ? 'text-2xl' : 'text-4xl'} leading-none`}>{scene.icon}</span>
              <span className="min-w-0">
                <span className={`block font-black ${compact ? 'text-sm' : 'text-xl'} ${active ? 'text-agri-800' : 'text-dark'}`}>
                  {scene.name}
                </span>
                <span className={`mt-1 block ${compact ? 'text-[11px]' : 'text-sm'} leading-relaxed ${active ? 'text-agri-700' : 'text-slate-500'}`}>
                  {scene.badge}
                </span>
              </span>
            </div>
            {!compact && (
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-500">
                <span className="rounded-md bg-white/70 px-2.5 py-2">{scene.terrain}</span>
                <span className="rounded-md bg-white/70 px-2.5 py-2">{scene.wind}</span>
              </div>
            )}
            {active && (
              <span className="absolute right-3 top-3 rounded-full bg-agri-500 px-2.5 py-1 text-xs font-bold text-white">
                当前场景
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
