import { createContext, useContext, useState } from 'react'
import { DEFAULT_SCENE_ID, SCENES, getSceneById } from '../data/scenes'

const AppContext = createContext()

export function AppProvider({ children }) {
  const [selectedApp, setSelectedApp] = useState(0)
  const [selectedSceneId, setSelectedSceneId] = useState(DEFAULT_SCENE_ID)
  const selectedScene = getSceneById(selectedSceneId)
  const [flightParams, setFlightParams] = useState({
    droneCount: 2,
    taskCount: 3,
    autoAssignment: true,
    initialBatteryPercent: 100,
    baseConsumptionPerMeter: 0.035,
    windSensitivity: 0.0015,
    startX: 5,
    startY: 3,
    endX: 85,
    endY: 60,
    droneName: 'UAV-01',
    droneX: 12.5,
    droneY: 8.0,
    droneZ: 15.0,
    battery: 92,
    speedCheck: true,
    obstacleCheck: true,
    altitudeCheck: false,
  })

  return (
    <AppContext.Provider value={{
      selectedApp, setSelectedApp,
      scenes: SCENES,
      selectedScene,
      selectedSceneId,
      setSelectedSceneId,
      flightParams, setFlightParams,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppContext() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useAppContext must be used within AppProvider')
  return ctx
}
