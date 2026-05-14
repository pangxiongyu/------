import { useMemo, useRef, useEffect } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { generateWaypoints } from '../../utils/flightPathGenerator'
import { useAppContext } from '../../context/AppContext'

export default function FlightPathLine() {
  const { flightParams } = useAppContext()
  const droneRef = useRef()
  const curveRef = useRef()

  const { curve, startPoint, endPoint, waypoints } = useMemo(() => {
    const start = { x: flightParams.startX, y: 3, z: flightParams.startY }
    const end = { x: flightParams.endX, y: 3, z: flightParams.endY }
    const wpts = generateWaypoints(start, end, 10)
    const pts = wpts.map((w) => new THREE.Vector3(w.x, w.y, w.z))
    const c = new THREE.CatmullRomCurve3(pts)
    return { curve: c, startPoint: pts[0], endPoint: pts[pts.length - 1], waypoints: wpts }
  }, [flightParams])

  // Store curve in ref for useFrame access
  useEffect(() => {
    curveRef.current = curve
  }, [curve])

  const tubeGeo = useMemo(() => {
    return new THREE.TubeGeometry(curve, 100, 0.2, 8, false)
  }, [curve])

  useFrame(({ clock }) => {
    if (droneRef.current && curveRef.current) {
      const t = (Math.sin(clock.getElapsedTime() * 0.3) + 1) / 2
      const pt = curveRef.current.getPointAt(t)
      droneRef.current.position.copy(pt)
      droneRef.current.position.y += 1.5
    }
  })

  return (
    <group>
      {/* Tube path */}
      <mesh geometry={tubeGeo}>
        <meshStandardMaterial color="#F59E0B" emissive="#F59E0B" emissiveIntensity={0.4} roughness={0.3} />
      </mesh>

      {/* Start marker */}
      <mesh position={startPoint}>
        <sphereGeometry args={[0.6, 16, 16]} />
        <meshStandardMaterial color="#10B981" emissive="#10B981" emissiveIntensity={0.6} />
      </mesh>

      {/* End marker */}
      <mesh position={endPoint}>
        <sphereGeometry args={[0.6, 16, 16]} />
        <meshStandardMaterial color="#EF4444" emissive="#EF4444" emissiveIntensity={0.6} />
      </mesh>

      {/* Waypoints */}
      {waypoints.filter((_, i) => i > 0 && i < waypoints.length - 1).map((wp, i) => (
        <mesh key={i} position={[wp.x, wp.y, wp.z]}>
          <sphereGeometry args={[0.25, 8, 8]} />
          <meshStandardMaterial color="#FBBF24" emissive="#FBBF24" emissiveIntensity={0.4} />
        </mesh>
      ))}

      {/* Animated drone */}
      <group ref={droneRef}>
        {/* Drone body */}
        <mesh>
          <boxGeometry args={[0.6, 0.15, 0.6]} />
          <meshStandardMaterial color="#1F2937" />
        </mesh>
        {/* Arms */}
        <mesh position={[0.5, 0, 0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151"/></mesh>
        <mesh position={[-0.5, 0, 0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151"/></mesh>
        <mesh position={[0.5, 0, -0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151"/></mesh>
        <mesh position={[-0.5, 0, -0.5]}><cylinderGeometry args={[0.04, 0.04, 1.2]} /><meshStandardMaterial color="#374151"/></mesh>
        {/* Propellers */}
        {[[0.5,0,0.5],[-0.5,0,0.5],[0.5,0,-0.5],[-0.5,0,-0.5]].map((pos, i) => (
          <AnimatedPropeller key={i} position={pos} />
        ))}
      </group>
    </group>
  )
}

function AnimatedPropeller({ position }) {
  const ref = useRef()
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 20
  })
  return (
    <mesh ref={ref} position={position}>
      <torusGeometry args={[0.22, 0.04, 8, 16]} />
      <meshStandardMaterial color="#9CA3AF" />
    </mesh>
  )
}
