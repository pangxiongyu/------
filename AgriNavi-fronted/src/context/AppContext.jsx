import { createContext, useContext, useState } from 'react';
import { defaultsceneid, scenes, getscenebyid } from '../data/scenes';
const AppContext = createContext();
export function AppProvider({
  children
}) {
  const [selectedapp, setselectedapp] = useState(0);
  const [selectedsceneid, setselectedsceneid] = useState(defaultsceneid);
  const selectedscene = getscenebyid(selectedsceneid);
  const [flightparams, setflightparams] = useState({
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
    altitudeCheck: false
  });
  return <AppContext.Provider value={{
    selectedApp: selectedapp,
    setSelectedApp: setselectedapp,
    scenes: scenes,
    selectedScene: selectedscene,
    selectedSceneId: selectedsceneid,
    setSelectedSceneId: setselectedsceneid,
    flightParams: flightparams,
    setFlightParams: setflightparams
  }}>
      {children}
    </AppContext.Provider>;
}
function useappcontext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used within AppProvider');
  return ctx;
}
export { useappcontext };
