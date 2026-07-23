import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { dronefleet } from '../../data/droneFleet';
function DroneModel({
  position
}) {
  const groupref = useRef();
  useFrame((unused, delta) => {
    if (groupref.current) {
      groupref.current.position.y += Math.sin(Date.now() * 0.003 + position[0]) * 0.005;
    }
  });
  return <group ref={groupref} position={position}>
      {/* 机身 */}
      <mesh>
        <boxGeometry args={[0.5, 0.1, 0.5]} />
        <meshStandardMaterial color="#3B82F6" emissive="#3B82F6" emissiveIntensity={0.3} />
      </mesh>
      {/* 提示光环 */}
      <mesh position={[0, -0.3, 0]}>
        <ringGeometry args={[0.3, 0.4, 32]} />
        <meshBasicMaterial color="#60A5FA" side={2} transparent opacity={0.6} />
      </mesh>
    </group>;
}
export default function DroneMarkers() {
  return <group>
      {dronefleet.map(drone => <DroneModel key={drone.id} position={[drone.x, drone.y + 2, drone.z]} />)}
    </group>;
}
