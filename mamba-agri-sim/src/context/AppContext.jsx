import { createContext, useContext, useState } from 'react'

const AppContext = createContext()

export function AppProvider({ children }) {
  const [selectedApp, setSelectedApp] = useState(0)
  const [flightParams, setFlightParams] = useState({
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
