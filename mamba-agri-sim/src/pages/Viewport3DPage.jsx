import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAppContext } from '../context/AppContext'
import { getSceneById } from '../data/scenes'

const DEFAULT_DRONE_ORCHARD_URL = '/drone-orchard/index.html'

function getDroneOrchardUrl() {
  const configuredUrl = import.meta.env.VITE_DRONE_ORCHARD_URL

  if (!configuredUrl) {
    return DEFAULT_DRONE_ORCHARD_URL
  }

  try {
    const target = new URL(configuredUrl, window.location.origin)
    const isCurrentAppRoot = target.origin === window.location.origin && target.pathname === '/'
    return isCurrentAppRoot ? DEFAULT_DRONE_ORCHARD_URL : configuredUrl
  } catch {
    return DEFAULT_DRONE_ORCHARD_URL
  }
}

export default function Viewport3DPage() {
  const location = useLocation()
  const { selectedSceneId, setSelectedSceneId } = useAppContext()
  const searchParams = new URLSearchParams(location.search)
  const requestedSceneId = searchParams.get('scene')
  const sceneId = requestedSceneId ? getSceneById(requestedSceneId).id : selectedSceneId
  const droneOrchardUrl = getDroneOrchardUrl()

  useEffect(() => {
    if (requestedSceneId && sceneId !== selectedSceneId) {
      setSelectedSceneId(sceneId)
    }
  }, [requestedSceneId, sceneId, selectedSceneId, setSelectedSceneId])

  searchParams.set('embed', '1')
  searchParams.set('scene', sceneId)
  const src = `${droneOrchardUrl}${droneOrchardUrl.includes('?') ? '&' : '?'}${searchParams.toString()}`

  return (
    <main className="min-h-screen overflow-hidden bg-[#07130f] pt-16">
      <div className="h-[calc(100vh-4rem)] w-full overflow-hidden bg-[#07130f]">
        <iframe
          title="无人机农业生产路径规划三维可视化"
          src={src}
          className="block h-full w-full border-0"
          allow="fullscreen; autoplay; xr-spatial-tracking"
          loading="eager"
        />
      </div>
    </main>
  )
}
