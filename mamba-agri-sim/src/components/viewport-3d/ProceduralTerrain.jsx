import { useMemo } from 'react'
import * as THREE from 'three'
import { generateHeightmap, getTerrainColor } from '../../utils/terrainGenerator'

const SIZE = 100
const RES = 128

export default function ProceduralTerrain() {
  const geometry = useMemo(() => {
    const heights = generateHeightmap(SIZE, SIZE, RES)
    const geo = new THREE.PlaneGeometry(SIZE, SIZE, RES - 1, RES - 1)
    geo.rotateX(-Math.PI / 2)

    const positions = geo.attributes.position
    const colors = new Float32Array(positions.count * 3)

    for (let i = 0; i < positions.count; i++) {
      const ix = i % RES
      const iz = Math.floor(i / RES)
      const h = heights[iz * RES + ix]
      positions.setY(i, h)
      const [r, g, b] = getTerrainColor(h)
      colors[i * 3] = r
      colors[i * 3 + 1] = g
      colors[i * 3 + 2] = b
    }

    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geo.computeVertexNormals()
    return geo
  }, [])

  return (
    <mesh geometry={geometry} receiveShadow>
      <meshStandardMaterial vertexColors side={THREE.DoubleSide} flatShading roughness={0.8} metalness={0.1}/>
    </mesh>
  )
}
