import { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Sky, Environment } from '@react-three/drei'
import ProceduralTerrain from './ProceduralTerrain'
import FlightPathLine from './FlightPathLine'
import DroneMarkers from './DroneMarkers'

function Scene({ flightParams }) {
  return (
    <>
      <Sky sunPosition={[100, 50, 100]} turbidity={8} rayleigh={2} />
      <ambientLight intensity={0.4} />
      <directionalLight
        position={[50, 40, 30]}
        intensity={1.2}
        castShadow
        shadow-mapSize={[1024, 1024]}
        shadow-camera-left={-60}
        shadow-camera-right={60}
        shadow-camera-top={60}
        shadow-camera-bottom={-60}
      />
      <hemisphereLight args={['#87CEEB', '#3B5323', 0.3]} />

      <ProceduralTerrain />
      <FlightPathLine flightParams={flightParams} />
      <DroneMarkers />

      <OrbitControls
        target={[45, 5, 20]}
        maxPolarAngle={Math.PI / 2.2}
        minDistance={20}
        maxDistance={120}
        enableDamping
        dampingFactor={0.1}
      />
      <Environment preset="sunset" />
    </>
  )
}

export default function TerrainScene({ flightParams }) {
  return (
    <div className="w-full h-full rounded-2xl overflow-hidden shadow-2xl">
      <Canvas
        camera={{ position: [80, 50, 60], fov: 50, near: 0.5, far: 300 }}
        shadows
        gl={{ antialias: true, alpha: false }}
        style={{ background: 'linear-gradient(180deg, #87CEEB 0%, #E0F2FE 100%)' }}
      >
        <Suspense fallback={null}>
          <Scene flightParams={flightParams} />
        </Suspense>
      </Canvas>
    </div>
  )
}
