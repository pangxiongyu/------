import { useMemo } from 'react';
import * as THREE from 'three';
import { generateheightmap, getterraincolor } from '../../utils/terrainGenerator';
const size = 100;
const res = 128;
export default function ProceduralTerrain() {
  const geometry = useMemo(() => {
    const heights = generateheightmap(size, size, res);
    const geo = new THREE.PlaneGeometry(size, size, res - 1, res - 1);
    geo.rotateX(-Math.PI / 2);
    const positions = geo.attributes.position;
    const colors = new Float32Array(positions.count * 3);
    for (let i = 0; i < positions.count; i++) {
      const ix = i % res;
      const iz = Math.floor(i / res);
      const h = heights[iz * res + ix];
      positions.setY(i, h);
      const [r, g, b] = getterraincolor(h);
      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    return geo;
  }, []);
  return <mesh geometry={geometry} receiveShadow>
      <meshStandardMaterial vertexColors side={THREE.DoubleSide} flatShading roughness={0.8} metalness={0.1} />
    </mesh>;
}
