import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useappcontext } from '../context/AppContext';
import { getscenebyid } from '../data/scenes';
const defaultdroneorchardurl = '/drone-orchard/index.html';
function getdroneorchardurl() {
  const configuredurl = import.meta.env.VITE_DRONE_ORCHARD_URL;
  if (!configuredurl) {
    return defaultdroneorchardurl;
  }
  try {
    const target = new URL(configuredurl, window.location.origin);
    const iscurrentapproot = target.origin === window.location.origin && target.pathname === '/';
    return iscurrentapproot ? defaultdroneorchardurl : configuredurl;
  } catch {
    return defaultdroneorchardurl;
  }
}
export default function Viewport3DPage() {
  const location = useLocation();
  const {
    flightParams: flightparams,
    selectedSceneId: selectedsceneid,
    setSelectedSceneId: setselectedsceneid
  } = useappcontext();
  const searchparams = new URLSearchParams(location.search);
  const requestedsceneid = searchparams.get('scene');
  const sceneid = requestedsceneid ? getscenebyid(requestedsceneid).id : selectedsceneid;
  const droneorchardurl = getdroneorchardurl();
  useEffect(() => {
    if (requestedsceneid && sceneid !== selectedsceneid) {
      setselectedsceneid(sceneid);
    }
  }, [requestedsceneid, sceneid, selectedsceneid, setselectedsceneid]);
  searchparams.set('embed', '1');
  searchparams.set('scene', sceneid);
  searchparams.set('drones', String(flightparams.droneCount));
  searchparams.set('tasks', String(flightparams.taskCount));
  searchparams.set('auto', String(flightparams.autoAssignment !== false));
  const src = `${droneorchardurl}${droneorchardurl.includes('?') ? '&' : '?'}${searchparams.toString()}`;
  return <main className="min-h-screen overflow-hidden bg-[#07130f] pt-16">
      <div className="h-[calc(100vh-4rem)] w-full overflow-hidden bg-[#07130f]">
        <iframe title="无人机农业生产路径规划三维可视化" src={src} className="block h-full w-full border-0" allow="fullscreen; autoplay; xr-spatial-tracking" loading="eager" />
      </div>
    </main>;
}
