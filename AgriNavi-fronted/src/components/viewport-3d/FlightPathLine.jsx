import { useMemo, useRef, useEffect } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { generatewaypoints } from '../../utils/flightPathGenerator';
export default function FlightPathLine({
  flightParams: flightparams
}) {
  const droneref = useRef();
  const curveref = useRef();
  const {
    startX: startx,
    startY: starty,
    endX: endx,
    endY: endy
  } = flightparams || {
    startX: 5,
    startY: 3,
    endX: 85,
    endY: 60
  };
  const {
    curve,
    startPoint: startpoint,
    endPoint: endpoint,
    waypoints
  } = useMemo(() => {
    const start = {
      x: startx,
      y: 3,
      z: starty
    };
    const end = {
      x: endx,
      y: 3,
      z: endy
    };
    const wpts = generatewaypoints(start, end, 10);
    const pts = wpts.map(w => new THREE.Vector3(w.x, w.y, w.z));
    const c = new THREE.CatmullRomCurve3(pts);
    return {
      curve: c,
      startPoint: pts[0],
      endPoint: pts[pts.length - 1],
      waypoints: wpts
    };
  }, [startx, starty, endx, endy]);
  useEffect(() => {
    curveref.current = curve;
  }, [curve]);
  const tubegeo = useMemo(() => {
    return new THREE.TubeGeometry(curve, 100, 0.2, 8, false);
  }, [curve]);
  useFrame(({
    clock
  }) => {
    if (droneref.current && curveref.current) {
      const t = (Math.sin(clock.getElapsedTime() * 0.3) + 1) / 2;
      const pt = curveref.current.getPointAt(t);
      droneref.current.position.copy(pt);
      droneref.current.position.y += 1.5;
    }
  });
  return <group>
      <mesh geometry={tubegeo}>
        <meshStandardMaterial color="#F59E0B" emissive="#F59E0B" emissiveIntensity={0.4} roughness={0.3} />
      </mesh>

      <mesh position={startpoint}>
        <sphereGeometry args={[0.6, 16, 16]} />
        <meshStandardMaterial color="#10B981" emissive="#10B981" emissiveIntensity={0.6} />
      </mesh>

      <mesh position={endpoint}>
        <sphereGeometry args={[0.6, 16, 16]} />
        <meshStandardMaterial color="#EF4444" emissive="#EF4444" emissiveIntensity={0.6} />
      </mesh>

      {waypoints.filter((unused, i) => i > 0 && i < waypoints.length - 1).map((wp, i) => <mesh key={i} position={[wp.x, wp.y, wp.z]}>
          <sphereGeometry args={[0.25, 8, 8]} />
          <meshStandardMaterial color="#FBBF24" emissive="#FBBF24" emissiveIntensity={0.4} />
        </mesh>)}

      <group ref={droneref}>
        <mesh>
          <boxGeometry args={[0.6, 0.15, 0.6]} />
          <meshStandardMaterial color="#1F2937" />
        </mesh>
        <mesh position={[0.5, 0, 0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151" /></mesh>
        <mesh position={[-0.5, 0, 0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151" /></mesh>
        <mesh position={[0.5, 0, -0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151" /></mesh>
        <mesh position={[-0.5, 0, -0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151" /></mesh>
        {[[0.5, 0, 0.5], [-0.5, 0, 0.5], [0.5, 0, -0.5], [-0.5, 0, -0.5]].map((pos, i) => <AnimatedPropeller key={i} position={pos} />)}
      </group>
    </group>;
}
function AnimatedPropeller({
  position
}) {
  const ref = useRef();
  useFrame((unused, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 20;
  });
  return <mesh ref={ref} position={position}>
      <torusGeometry args={[0.22, 0.04, 8, 16]} />
      <meshStandardMaterial color="#9CA3AF" />
    </mesh>;
}
