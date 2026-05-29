import { useState, useMemo, useRef, useEffect, useCallback, type CSSProperties } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky } from '@react-three/drei';
import * as THREE from 'three';

// 核心参数
const ORCHARD_SIZE = 140; 
const ROW_SPACING = 18;   
const TREE_SPACING = 10;   
const MAIN_ROAD_WIDTH = 8; 
const DRONE_HOVER_HEIGHT = 6;

type WindLayer = {
  id: string;
  label: string;
  height: number;
  speed: number;
  direction: number;
  color: string;
  note: string;
};

const DEFAULT_WIND_LAYERS: WindLayer[] = [
  {
    id: "near-ground",
    label: "近地层",
    height: 35,
    speed: 3.2,
    direction: 45,
    color: "#4caf50",
    note: "低空作业扰动较小",
  },
  {
    id: "operation",
    label: "作业层",
    height: 70,
    speed: 6.8,
    direction: 110,
    color: "#ffb300",
    note: "无人机主要巡航高度",
  },
  {
    id: "upper",
    label: "高空层",
    height: 115,
    speed: 10.5,
    direction: 230,
    color: "#e53935",
    note: "风速较大，路径代价更高",
  },
];

const SCENE_OPTIONS = [
  { id: 'modern', label: '平原果园', icon: '🍎' },
  { id: 'terrace', label: '高山梯田', icon: '🌾' },
] as const;

// --- 地形数学函数 ---
const getTerrainHeight = (x: number, z: number, type: 'modern' | 'terrace') => {
  if (type === 'modern') {
    let y = Math.sin(x * 0.008) * Math.cos(z * 0.012) * 18;
    y += Math.sin(x * 0.03 + z * 0.02) * 5;
    y += Math.sin(x * 0.1) * Math.cos(z * 0.1) * 0.5;
    return y + 25; 
  } else {
    // 梯田：高低落差极大，层层递进
    let rawY = Math.sin(x * 0.008) * Math.cos(z * 0.01) * 60;
    rawY += Math.sin(x * 0.02 + z * 0.02) * 20;
    rawY += 70; 
    
    const step = 8; // 每层梯田的高度落差
    const terraceY = Math.floor(rawY / step) * step;
    const remainder = rawY % step;
    
    // 85% 是平整的田面，15% 是垂直/陡峭的田埂
    const edge = step * 0.85; 
    if (remainder > edge) {
       const t = (remainder - edge) / (step - edge);
       const smoothT = t * t * (3 - 2 * t);
       return terraceY + smoothT * step;
    } else {
       // 平坦田面
       return terraceY; 
    }
  }
};

// --- 地形网格组件 ---
const Terrain = ({ sceneType, onPointerDown }: { sceneType: 'modern' | 'terrace', onPointerDown?: (e: any) => void }) => {
  const geometry = useMemo(() => {
    const segments = sceneType === 'terrace' ? 400 : 250; // 梯田需要超高细分度来表现锐利的阶梯边缘
    const geo = new THREE.PlaneGeometry(400, 400, segments, segments);
    geo.rotateX(-Math.PI / 2);
    
    const pos = geo.attributes.position;
    const colors = [];
    
    const colorRoad = new THREE.Color("#bfae83"); 
    const colorSoil = new THREE.Color("#4a3525"); 
    const colorGrass1 = new THREE.Color("#5a8231"); 
    const colorGrass2 = new THREE.Color("#688f3e"); 
    const colorWildGrass = new THREE.Color("#4a6b2c");

    // 梯田水稻田颜色：以黄绿稻苗、浅泥色水田和深褐田埂为主，避免大面积蓝色像湖面
    const colorTerraceRice = new THREE.Color("#8fbf3c"); // 水稻苗黄绿色
    const colorTerracePaddy = new THREE.Color("#8a7a4a"); // 浅泥色水田底色
    const colorTerraceWall = new THREE.Color("#524535"); // 湿润的深褐色陡峭田埂

    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      const y = getTerrainHeight(x, z, sceneType);
      pos.setY(i, y);
      
      const c = new THREE.Color();
      
      if (sceneType === 'modern') {
        const isMainRoadX = Math.abs(x) < MAIN_ROAD_WIDTH;
        const isMainRoadZ = Math.abs(z) < MAIN_ROAD_WIDTH;
        const inOrchard = Math.abs(x) < ORCHARD_SIZE && Math.abs(z) < ORCHARD_SIZE;
        const nearestRowX = Math.round(x / ROW_SPACING) * ROW_SPACING;
        const distToRow = Math.abs(x - nearestRowX);
        const isTreeRow = distToRow < 2.2 && inOrchard;

        if (isMainRoadX || isMainRoadZ) {
          c.copy(colorRoad);
        } else if (inOrchard) {
          if (isTreeRow) {
            c.copy(colorSoil);
          } else {
            c.lerpColors(colorGrass1, colorGrass2, Math.min(y / 40, 1));
          }
        } else {
          c.copy(colorWildGrass);
        }
      } else {
        // 梯田：水稻田风貌
        const dx = getTerrainHeight(x + 0.1, z, sceneType) - y;
        const dz = getTerrainHeight(x, z + 0.1, sceneType) - y;
        const slope = Math.sqrt(dx * dx + dz * dz) * 10; 
        
        if (slope > 6) {
          // 陡峭的田埂
          c.copy(colorTerraceWall);
        } else {
          // 平坦的田面，模拟水稻苗覆盖下的浅泥色水田
          const factor = (Math.sin(x * 0.5 + z * 0.5) + 1) / 2; 
          c.lerpColors(colorTerraceRice, colorTerracePaddy, factor * 0.35);
        }
      }
      
      c.offsetHSL(0, 0, (Math.random() - 0.5) * 0.04);
      colors.push(c.r, c.g, c.b);
    }
    
    geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    return geo;
  }, [sceneType]);

  return (
    <mesh geometry={geometry} receiveShadow onPointerDown={onPointerDown}>
      <meshStandardMaterial 
        vertexColors 
        roughness={sceneType === 'terrace' ? 0.9 : 0.95} 
        metalness={0.02} 
        flatShading={true} 
      />
    </mesh>
  );
};

const WindArrow = ({ layer, x, z }: { layer: WindLayer, x: number, z: number }) => {
  const groupRef = useRef<THREE.Group>(null);
  const directionRad = THREE.MathUtils.degToRad(layer.direction);
  const driftDirection = useMemo(
    () => new THREE.Vector3(0, 0, 1).applyEuler(new THREE.Euler(0, -directionRad, 0)).normalize(),
    [directionRad]
  );
  const length = 6 + layer.speed * 0.7;

  useFrame((state) => {
    if (groupRef.current) {
      const cycleDistance = 34;
      const driftSpeed = 3 + layer.speed * 0.55;
      const phase = ((state.clock.elapsedTime * driftSpeed + x * 0.17 + z * 0.11) % cycleDistance) - cycleDistance / 2;
      const base = new THREE.Vector3(x, layer.height, z);
      const drift = driftDirection.clone().multiplyScalar(phase);
      groupRef.current.position.copy(base.add(drift));
      groupRef.current.position.y += Math.sin(state.clock.elapsedTime * 1.8 + x * 0.04 + z * 0.03) * 1.1;
    }
  });

  return (
    <group ref={groupRef} position={[x, layer.height, z]} rotation={[0, -directionRad, 0]}>
      <mesh position={[0, 0, length / 2]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.12, length, 8]} />
        <meshBasicMaterial color={layer.color} transparent opacity={0.55} />
      </mesh>
      <mesh position={[0, 0, length + 0.8]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <coneGeometry args={[0.65, 1.6, 12]} />
        <meshBasicMaterial color={layer.color} transparent opacity={0.85} />
      </mesh>
    </group>
  );
};

const WindLayerVisualization = ({ layers }: { layers: WindLayer[] }) => {
  const positions = [-80, 0, 80];

  return (
    <>
      {layers.map((layer) =>
        positions.map((x) =>
          positions.map((z) => (
            <WindArrow key={`${layer.id}-${x}-${z}`} layer={layer} x={x} z={z} />
          ))
        )
      )}
    </>
  );
};

const WindLayerPanel = ({
  layers,
  onChange,
  compact = false,
}: {
  layers: WindLayer[];
  onChange: (id: string, field: "speed" | "direction", value: number) => void;
  compact?: boolean;
}) => {
  if (compact) {
    return (
      <div style={{
        position: 'absolute',
        top: '58px',
        left: '10px',
        zIndex: 12,
        width: '150px',
        background: 'rgba(255,255,255,0.9)',
        borderRadius: '8px',
        padding: '8px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
        fontFamily: 'Inter, "Noto Sans SC", "Microsoft YaHei", sans-serif',
        backdropFilter: 'blur(10px)',
      }}>
        <div style={{ fontWeight: 'bold', fontSize: '12px', marginBottom: '6px', color: '#1b5e20' }}>
          风场高度层
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {layers.map((layer) => (
            <div key={layer.id} style={{ borderLeft: `4px solid ${layer.color}`, background: '#f7faf7', borderRadius: '6px', padding: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', fontWeight: 'bold' }}>
                <span>{layer.label}</span>
                <span>{layer.height}m</span>
              </div>
              <div style={{ fontSize: '10px', color: '#444', marginTop: '3px' }}>
                {layer.speed.toFixed(1)} m/s · {layer.direction}°
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: 'absolute', top: '70px', left: '20px', zIndex: 12, width: '230px', background: 'rgba(255,255,255,0.92)', borderRadius: '10px', padding: '14px', boxShadow: '0 4px 12px rgba(0,0,0,0.18)', fontFamily: 'sans-serif' }}>
      <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '10px', color: '#1b5e20' }}>
        风场高度层
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {layers.map((layer) => (
          <div key={layer.id} style={{ borderLeft: `5px solid ${layer.color}`, background: '#f7faf7', borderRadius: '6px', padding: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 'bold' }}>
              <span>{layer.label}</span>
              <span>{layer.height}m</span>
            </div>
            <div style={{ fontSize: '11px', color: '#444', marginTop: '6px', lineHeight: 1.5 }}>
              <label style={{ display: 'block', marginBottom: '4px' }}>
                风速 m/s
                <input
                  type="number"
                  min="0"
                  max="30"
                  step="0.1"
                  value={layer.speed}
                  onChange={(event) => onChange(layer.id, "speed", Number(event.target.value))}
                  style={{ width: '100%', boxSizing: 'border-box', marginTop: '2px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              </label>
              <label style={{ display: 'block', marginBottom: '4px' }}>
                风向 °
                <input
                  type="number"
                  min="0"
                  max="360"
                  step="1"
                  value={layer.direction}
                  onChange={(event) => onChange(layer.id, "direction", Number(event.target.value))}
                  style={{ width: '100%', boxSizing: 'border-box', marginTop: '2px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              </label>
              {layer.note}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// --- 梯田农作物组件 (水稻丛) ---
const CropInstanced = ({ count, type }: { count: number, type: 'modern' | 'terrace' }) => {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  
  useEffect(() => {
    if (!meshRef.current || type !== 'terrace') return;
    
    const dummy = new THREE.Object3D();
    let placed = 0;
    
    // 我们将水稻成簇地种在梯田上
    // 水稻间距相对固定，可以模拟人工插秧的网格感
    for (let x = -180; x <= 180; x += 2.4) {
      for (let z = -180; z <= 180; z += 2.4) {
        if (placed >= count) break;
        
        // 允许有一点点不规则的插秧偏移
        const px = x + (Math.random() - 0.5) * 0.3;
        const pz = z + (Math.random() - 0.5) * 0.3;
        const y = getTerrainHeight(px, pz, 'terrace');
        
        // 计算坡度
        const dx = getTerrainHeight(px + 0.1, pz, 'terrace') - y;
        const dz = getTerrainHeight(px, pz + 0.1, 'terrace') - y;
        const slope = Math.sqrt(dx*dx + dz*dz) * 10;

        // 梯田水稻只种在平坦的、有水的田面上
        if (slope < 1.5) {
          dummy.position.set(px, y + 0.4, pz);
          // 水稻丛的自然缩放
          const scale = 0.8 + Math.random() * 0.4;
          dummy.scale.set(scale, scale * (1 + Math.random() * 0.3), scale);
          dummy.rotation.y = Math.random() * Math.PI;
          // 让水稻有随风轻微倾斜的感觉
          dummy.rotation.x = (Math.random() - 0.5) * 0.1;
          dummy.rotation.z = (Math.random() - 0.5) * 0.1;
          
          dummy.updateMatrix();
          meshRef.current.setMatrixAt(placed, dummy.matrix);
          placed++;
        }
      }
      if (placed >= count) break;
    }
    meshRef.current.count = placed;
    meshRef.current.instanceMatrix.needsUpdate = true;
  }, [count, type]);

  if (type !== 'terrace') return null;

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, count]} castShadow receiveShadow>
      {/* 使用细长而顶部略尖的圆柱体组合模拟一簇水稻苗 */}
      <cylinderGeometry args={[0.05, 0.15, 1.2, 5]} />
      <meshStandardMaterial color="#88c930" roughness={0.7} flatShading />
    </instancedMesh>
  );
};

// --- 苹果树与防风林 ---
const ModernAppleTree = ({ position }: { position: [number, number, number] }) => {
  return (
    <group position={position}>
      <mesh position={[0, 1.5, 0]} castShadow>
        <cylinderGeometry args={[0.1, 0.15, 3, 5]} />
        <meshStandardMaterial color="#4a3520" flatShading />
      </mesh>
      <mesh position={[0, 2.0, 0]} castShadow>
        <dodecahedronGeometry args={[1.3, 0]} />
        <meshStandardMaterial color="#355e25" flatShading />
      </mesh>
      <mesh position={[0, 3.2, 0]} castShadow>
        <dodecahedronGeometry args={[1.0, 0]} />
        <meshStandardMaterial color="#41732e" flatShading />
      </mesh>
      <mesh position={[0, 4.2, 0]} castShadow>
        <dodecahedronGeometry args={[0.7, 0]} />
        <meshStandardMaterial color="#4a8036" flatShading />
      </mesh>
      {[
        [0.9, 2.0, 0.5], [-0.9, 2.2, -0.4], [0.4, 3.2, 0.8], 
        [-0.6, 3.0, 0.6], [0.5, 4.0, -0.3], [0, 2.5, -1.1]
      ].map((pos, i) => (
        <mesh key={i} position={pos as [number, number, number]} castShadow>
          <icosahedronGeometry args={[0.12, 0]} />
          <meshStandardMaterial color="#d93838" flatShading />
        </mesh>
      ))}
    </group>
  );
};

const PoplarTree = ({ position }: { position: [number, number, number] }) => {
  return (
    <group position={position}>
      <mesh position={[0, 1.5, 0]} castShadow>
        <cylinderGeometry args={[0.2, 0.3, 3, 5]} />
        <meshStandardMaterial color="#3b2b1c" flatShading />
      </mesh>
      <mesh position={[0, 6, 0]} castShadow>
        <cylinderGeometry args={[0.1, 1.2, 10, 6]} />
        <meshStandardMaterial color="#2d4c1e" flatShading />
      </mesh>
    </group>
  );
};

// --- 基础设施与点缀 ---
const Helipad = ({ position }: { position: [number, number, number] }) => {
  return (
    <group position={position}>
      <mesh position={[0, 0, 0]} receiveShadow castShadow>
        <cylinderGeometry args={[6, 6, 8, 32]} />
        <meshStandardMaterial color="#555555" />
      </mesh>
      <mesh position={[0, 4.01, 0]} rotation={[-Math.PI/2, 0, 0]} receiveShadow>
        <ringGeometry args={[4.8, 5.5, 32]} />
        <meshBasicMaterial color="#ffb300" />
      </mesh>
      <group position={[0, 4.02, 0]} rotation={[-Math.PI/2, 0, 0]}>
        <mesh position={[-1.5, 0, 0]}>
          <planeGeometry args={[0.6, 4]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
        <mesh position={[1.5, 0, 0]}>
          <planeGeometry args={[0.6, 4]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
        <mesh position={[0, 0, 0]} rotation={[0, 0, Math.PI/2]}>
          <planeGeometry args={[0.6, 3]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      </group>
    </group>
  );
};

const FarmHouse = ({ position }: { position: [number, number, number] }) => {
  return (
    <group position={position}>
      <mesh position={[0, -0.5, 0]} castShadow receiveShadow>
        <boxGeometry args={[16, 5, 10]} />
        <meshStandardMaterial color="#cccccc" />
      </mesh>
      <mesh position={[0, 4, 0]} castShadow receiveShadow>
        <boxGeometry args={[15, 6, 9]} />
        <meshStandardMaterial color="#e0d0b8" flatShading />
      </mesh>
      <mesh position={[0, 8.5, 0]} rotation={[0, Math.PI / 4, 0]} castShadow>
        <coneGeometry args={[11, 4, 4]} />
        <meshStandardMaterial color="#2c5e8c" flatShading />
      </mesh>
      <mesh position={[0, 3, 4.6]} castShadow>
        <boxGeometry args={[4, 3, 0.2]} />
        <meshStandardMaterial color="#4477aa" roughness={0.1} metalness={0.8} />
      </mesh>
    </group>
  );
};

// --- 无人机及其连续多任务飞行逻辑 ---
const MultiLegDrone = ({
  uavId,
  waypoints,
  speed = 25,
  isSimulating,
  sceneType,
  energyProfile,
  windLayers,
  onTelemetry,
}: {
  uavId: string;
  waypoints: THREE.Vector3[];
  speed?: number;
  isSimulating: boolean;
  sceneType: 'modern' | 'terrace';
  energyProfile: DroneEnergyProfile;
  windLayers: WindLayer[];
  onTelemetry: (uavId: string, telemetry: DroneTelemetry) => void;
}) => {
  const droneRef = useRef<THREE.Group>(null);
  const progressRef = useRef(0);
  const legIndexRef = useRef(0);
  const traveledDistanceRef = useRef(0);
  const baseConsumedRef = useRef(0);
  const windExtraConsumedRef = useRef(0);
  const telemetryTimerRef = useRef(0);
  const previousPositionRef = useRef<THREE.Vector3 | null>(null);
  const hasCompletedRef = useRef(false);

  const totalDistance = useMemo(() => {
    if (waypoints.length < 2) return 0;
    let sum = 0;
    for (let i = 0; i < waypoints.length - 1; i += 1) {
      sum += waypoints[i].distanceTo(waypoints[i + 1]);
    }
    return sum;
  }, [waypoints]);

  const hoverPoint = (point: THREE.Vector3) => new THREE.Vector3(point.x, point.y + DRONE_HOVER_HEIGHT, point.z);

  useEffect(() => {
    progressRef.current = 0;
    legIndexRef.current = 0;
    traveledDistanceRef.current = 0;
    baseConsumedRef.current = 0;
    windExtraConsumedRef.current = 0;
    telemetryTimerRef.current = 0;
    previousPositionRef.current = null;
    hasCompletedRef.current = false;
    onTelemetry(uavId, {
      batteryPercent: energyProfile.initialBatteryPercent,
      consumedPercent: 0,
      baseConsumedPercent: 0,
      windExtraConsumedPercent: 0,
      traveledDistance: 0,
      totalDistance,
      currentWindSpeed: 0,
      isComplete: false,
    });
  }, [isSimulating, waypoints, uavId, totalDistance, energyProfile.initialBatteryPercent, onTelemetry]);

  useFrame((state, delta) => {
    if (!droneRef.current || waypoints.length === 0) return;
    const currentLegIndex = Math.min(legIndexRef.current, Math.max(waypoints.length - 2, 0));
    const start = waypoints[currentLegIndex];
    const end = waypoints[Math.min(currentLegIndex + 1, waypoints.length - 1)];
    
    if (!isSimulating || waypoints.length === 1) {
      const pos = hoverPoint(waypoints[0]);
      droneRef.current.position.copy(pos);
      droneRef.current.position.y += Math.sin(state.clock.elapsedTime * 5) * 0.08;
      previousPositionRef.current = pos.clone();
      return;
    }

    if (progressRef.current >= 1) {
      if (currentLegIndex < waypoints.length - 2) {
        legIndexRef.current += 1;
        progressRef.current = 0;
      } else {
        droneRef.current.position.copy(hoverPoint(end));
        droneRef.current.position.y += Math.sin(state.clock.elapsedTime * 5) * 0.08;
        if (!hasCompletedRef.current) {
          const consumedPercent = Math.min(
            baseConsumedRef.current + windExtraConsumedRef.current,
            energyProfile.initialBatteryPercent
          );
          const batteryPercent = Math.max(energyProfile.initialBatteryPercent - consumedPercent, 0);
          onTelemetry(uavId, {
            batteryPercent,
            consumedPercent,
            baseConsumedPercent: baseConsumedRef.current,
            windExtraConsumedPercent: windExtraConsumedRef.current,
            traveledDistance: traveledDistanceRef.current,
            totalDistance,
            currentWindSpeed: 0,
            isComplete: true,
          });
          hasCompletedRef.current = true;
        }
      }
      return;
    }

    const distance = Math.max(start.distanceTo(end), 0.001);
    progressRef.current = Math.min(progressRef.current + (delta * speed) / distance, 1);

    const currentPos = new THREE.Vector3().lerpVectors(start, end, progressRef.current);
    const terrainY = getTerrainHeight(currentPos.x, currentPos.z, sceneType);
    
    const baseFlyHeight = terrainY + (sceneType === 'terrace' ? 30 : 15); 
    const arcHeight = Math.sin(progressRef.current * Math.PI) * (sceneType === 'terrace' ? 40 : 20);
    const hoverBaseline = THREE.MathUtils.lerp(
      start.y + DRONE_HOVER_HEIGHT,
      end.y + DRONE_HOVER_HEIGHT,
      progressRef.current
    );
    
    const flyHeight = Math.max(
      terrainY + DRONE_HOVER_HEIGHT,
      hoverBaseline + arcHeight,
      baseFlyHeight
    );

    currentPos.y = flyHeight;
    droneRef.current.position.copy(currentPos);

    if (previousPositionRef.current) {
      const stepDistance = previousPositionRef.current.distanceTo(currentPos);
      if (Number.isFinite(stepDistance)) {
        traveledDistanceRef.current += stepDistance;
        baseConsumedRef.current += stepDistance * energyProfile.baseConsumptionPerMeter;

        const sampledWind = sampleWindAtHeight(windLayers, currentPos.y);
        const horizontalMove = new THREE.Vector3(currentPos.x - previousPositionRef.current.x, 0, currentPos.z - previousPositionRef.current.z);
        const moveLen = horizontalMove.length();
        if (moveLen > 0.0001) {
          const moveDir = horizontalMove.normalize();
          const againstFactor = Math.max(moveDir.dot(sampledWind.vector.clone().multiplyScalar(-1)), 0);
          const windPenaltyPerMeter = sampledWind.speed * againstFactor * energyProfile.windSensitivity;
          windExtraConsumedRef.current += stepDistance * windPenaltyPerMeter;
        }
      }
    }
    previousPositionRef.current = currentPos.clone();

    const sampledWind = sampleWindAtHeight(windLayers, currentPos.y);
    const consumedPercent = Math.min(
      baseConsumedRef.current + windExtraConsumedRef.current,
      energyProfile.initialBatteryPercent
    );
    const batteryPercent = Math.max(energyProfile.initialBatteryPercent - consumedPercent, 0);
    telemetryTimerRef.current += delta;
    if (telemetryTimerRef.current >= 0.15) {
      onTelemetry(uavId, {
        batteryPercent,
        consumedPercent,
        baseConsumedPercent: baseConsumedRef.current,
        windExtraConsumedPercent: windExtraConsumedRef.current,
        traveledDistance: traveledDistanceRef.current,
        totalDistance,
        currentWindSpeed: sampledWind.speed,
        isComplete: false,
      });
      telemetryTimerRef.current = 0;
    }
    
    if (progressRef.current < 1) {
      droneRef.current.lookAt(end.x, droneRef.current.position.y, end.z);
    } else {
      droneRef.current.position.y += Math.sin(state.clock.elapsedTime * 15) * 0.05;
    }
  });

  const initialPosition = waypoints[0] ?? new THREE.Vector3();

  return (
    <group ref={droneRef} position={initialPosition} scale={[2.4, 2.4, 2.4]}>
      {/* 醒目的黄色机身，便于在大场景中识别 */}
      <mesh castShadow>
        <boxGeometry args={[0.9, 0.22, 0.9]} />
        <meshStandardMaterial color="#ffd54f" emissive="#5f4700" emissiveIntensity={0.25} metalness={0.35} roughness={0.25} flatShading />
      </mesh>

      {/* 蓝色外框和航行灯增强可见度 */}
      <mesh position={[0, 0.18, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.75, 0.035, 8, 36]} />
        <meshBasicMaterial color="#00bcd4" transparent opacity={0.85} />
      </mesh>
      <mesh position={[0, 0.2, 0.42]}>
        <sphereGeometry args={[0.1]} />
        <meshBasicMaterial color="#00ff66" />
      </mesh>
      <mesh position={[0, 0.2, -0.42]}>
        <sphereGeometry args={[0.1]} />
        <meshBasicMaterial color="#ff1744" />
      </mesh>

      {/* 十字机臂 */}
      <mesh position={[0, 0.03, 0]}>
        <boxGeometry args={[1.65, 0.08, 0.12]} />
        <meshStandardMaterial color="#263238" />
      </mesh>
      <mesh position={[0, 0.03, 0]}>
        <boxGeometry args={[0.12, 0.08, 1.65]} />
        <meshStandardMaterial color="#263238" />
      </mesh>

      {/* 四个更大的旋翼盘 */}
      {[
        [0.75, 0.75], [-0.75, -0.75], [0.75, -0.75], [-0.75, 0.75]
      ].map(([x, z], i) => (
        <group key={i} position={[x, 0.18, z]}>
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[0.28, 0.035, 8, 24]} />
            <meshBasicMaterial color="#111111" transparent opacity={0.75} />
          </mesh>
          <mesh rotation={[0, 0, Math.PI / 4]}>
            <boxGeometry args={[0.62, 0.025, 0.08]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={0.75} />
          </mesh>
          <mesh rotation={[0, 0, -Math.PI / 4]}>
            <boxGeometry args={[0.62, 0.025, 0.08]} />
            <meshBasicMaterial color="#ffffff" transparent opacity={0.75} />
          </mesh>
          <mesh position={[0, -0.12, 0]}>
            <cylinderGeometry args={[0.035, 0.035, 0.28]} />
            <meshStandardMaterial color="#666666" />
          </mesh>
        </group>
      ))}
    </group>
  );
};

const Marker = ({ position, type }: { position: THREE.Vector3, type: 'start' | 'end' }) => {
  const color = type === 'start' ? '#4CAF50' : '#F44336';
  return (
    <group position={position}>
      <mesh rotation={[-Math.PI/2, 0, 0]} position={[0, 0.2, 0]}>
        <ringGeometry args={[0.5, 1, 32]} />
        <meshBasicMaterial color={color} side={THREE.DoubleSide} transparent opacity={0.8} />
      </mesh>
      <mesh position={[0, 2.5, 0]}>
        <octahedronGeometry args={[0.4]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
      </mesh>
      <mesh position={[0, 1.25, 0]}>
        <cylinderGeometry args={[0.05, 0.05, 2.5]} />
        <meshBasicMaterial color={color} transparent opacity={0.5} />
      </mesh>
    </group>
  );
};

type RouteConfig = {
  id: string;
  uavId: string;
  taskId: string;
  start: THREE.Vector3;
  end: THREE.Vector3;
};

type DroneStart = {
  id: string;
  position: THREE.Vector3;
};

type TaskTarget = {
  id: string;
  position: THREE.Vector3;
};

type DroneEnergyProfile = {
  initialBatteryPercent: number;
  baseConsumptionPerMeter: number;
  windSensitivity: number;
};

type DroneTelemetry = {
  batteryPercent: number;
  consumedPercent: number;
  baseConsumedPercent: number;
  windExtraConsumedPercent: number;
  traveledDistance: number;
  totalDistance: number;
  currentWindSpeed: number;
  isComplete: boolean;
};

const windDirectionToVector = (directionDeg: number) => {
  const rad = THREE.MathUtils.degToRad(directionDeg);
  return new THREE.Vector3(0, 0, 1).applyEuler(new THREE.Euler(0, -rad, 0)).normalize();
};

const sampleWindAtHeight = (layers: WindLayer[], height: number) => {
  if (layers.length === 0) {
    return { speed: 0, vector: new THREE.Vector3(0, 0, 0) };
  }

  const sorted = [...layers].sort((a, b) => a.height - b.height);
  if (height <= sorted[0].height) {
    const vector = windDirectionToVector(sorted[0].direction);
    return { speed: sorted[0].speed, vector };
  }
  if (height >= sorted[sorted.length - 1].height) {
    const vector = windDirectionToVector(sorted[sorted.length - 1].direction);
    return { speed: sorted[sorted.length - 1].speed, vector };
  }

  for (let i = 0; i < sorted.length - 1; i += 1) {
    const low = sorted[i];
    const high = sorted[i + 1];
    if (height >= low.height && height <= high.height) {
      const t = (height - low.height) / Math.max(high.height - low.height, 0.001);
      const lowWind = windDirectionToVector(low.direction).multiplyScalar(low.speed);
      const highWind = windDirectionToVector(high.direction).multiplyScalar(high.speed);
      const blended = new THREE.Vector3().lerpVectors(lowWind, highWind, t);
      const speed = blended.length();
      return {
        speed,
        vector: speed > 0.0001 ? blended.normalize() : new THREE.Vector3(0, 0, 0),
      };
    }
  }

  const fallback = sorted[0];
  return { speed: fallback.speed, vector: windDirectionToVector(fallback.direction) };
};

// ==========================================
// 主应用入口：支持多界面导航
// ==========================================
export default function App() {
  const isEmbedded = useMemo(() => {
    return new URLSearchParams(window.location.search).get('embed') === '1';
  }, []);
  const initialSceneType = useMemo<'modern' | 'terrace'>(() => {
    const scene = new URLSearchParams(window.location.search).get('scene');
    return scene === 'terrace' ? 'terrace' : 'modern';
  }, []);
  const initialRouteConfig = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const numericParam = (key: string, fallback: number, min: number, max: number) => {
      const raw = Number(params.get(key));
      if (!Number.isFinite(raw)) return fallback;
      return Math.min(max, Math.max(min, raw));
    };

    return {
      droneCount: numericParam('drones', 2, 1, 12),
      taskCount: numericParam('tasks', 3, 1, 20),
      autoAssignment: params.get('auto') !== 'false',
      energyDefaults: {
        initialBatteryPercent: numericParam('battery', 100, 1, 100),
        baseConsumptionPerMeter: numericParam('consumption', 0.035, 0.01, 5),
        windSensitivity: numericParam('windSensitivity', 0.0015, 0, 0.2),
      },
    };
  }, []);
  const [viewportSize, setViewportSize] = useState(() => ({
    width: window.innerWidth,
    height: window.innerHeight,
  }));
  // page 状态扩展为：'home' (首页选择) | 'setup' | 'simulation'
  const [page, setPage] = useState<'home' | 'setup' | 'simulation'>(isEmbedded ? 'setup' : 'home');
  const [sceneType, setSceneType] = useState<'modern' | 'terrace'>(initialSceneType);

  const [windLayers, setWindLayers] = useState<WindLayer[]>(DEFAULT_WIND_LAYERS);
  const [droneCount, setDroneCount] = useState(initialRouteConfig.droneCount);
  const [taskCount, setTaskCount] = useState(initialRouteConfig.taskCount);
  const [droneStarts, setDroneStarts] = useState<DroneStart[]>([]);
  const [taskTargets, setTaskTargets] = useState<TaskTarget[]>([]);
  const [routes, setRoutes] = useState<RouteConfig[]>([]);
  const [setupMode, setSetupMode] = useState<'droneStart' | 'taskTarget' | null>(null);
  const [droneEnergyProfiles, setDroneEnergyProfiles] = useState<Record<string, DroneEnergyProfile>>({});
  const [droneTelemetry, setDroneTelemetry] = useState<Record<string, DroneTelemetry>>({});
  const isCompactLayout = viewportSize.width < 760;

  useEffect(() => {
    const handleResize = () => {
      setViewportSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const enterScene = (type: 'modern' | 'terrace') => {
    setSceneType(type);
    setRoutes([]);
    setSetupMode(null);
    setDroneStarts([]);
    setTaskTargets([]);
    setDroneTelemetry({});
    setPage('setup');
  };

  // 场景生态元素
  const elements = useMemo(() => {
    const el: { type: string, pos: [number, number, number] }[] = [];
    
    if (sceneType === 'modern') {
      for (let x = -ORCHARD_SIZE; x <= ORCHARD_SIZE; x += ROW_SPACING) {
        for (let z = -ORCHARD_SIZE; z <= ORCHARD_SIZE; z += TREE_SPACING) {
          if (Math.abs(x) < MAIN_ROAD_WIDTH + 2 || Math.abs(z) < MAIN_ROAD_WIDTH + 2) continue;
          const jx = x + (Math.random() - 0.5) * 0.4;
          const jz = z + (Math.random() - 0.5) * 0.4;
          const y = getTerrainHeight(jx, jz, sceneType);
          el.push({ type: 'apple', pos: [jx, y, jz] });
        }
      }
      for (let x = -ORCHARD_SIZE - 8; x <= ORCHARD_SIZE + 8; x += 8) {
        el.push({ type: 'poplar', pos: [x, getTerrainHeight(x, -ORCHARD_SIZE - 8, sceneType), -ORCHARD_SIZE - 8] });
        el.push({ type: 'poplar', pos: [x, getTerrainHeight(x, ORCHARD_SIZE + 8, sceneType), ORCHARD_SIZE + 8] });
      }
      for (let z = -ORCHARD_SIZE - 8; z <= ORCHARD_SIZE + 8; z += 8) {
        if (Math.abs(z) > ORCHARD_SIZE + 4) continue;
        el.push({ type: 'poplar', pos: [-ORCHARD_SIZE - 8, getTerrainHeight(-ORCHARD_SIZE - 8, z, sceneType), z] });
        el.push({ type: 'poplar', pos: [ORCHARD_SIZE + 8, getTerrainHeight(ORCHARD_SIZE + 8, z, sceneType), z] });
      }
      el.push({ type: 'helipad', pos: [0, getTerrainHeight(0, 0, sceneType), 0] });
      const h1x = 0, h1z = ORCHARD_SIZE + 15;
      el.push({ type: 'farmhouse', pos: [h1x, getTerrainHeight(h1x, h1z, sceneType), h1z] });
      const h2x = ORCHARD_SIZE + 15, h2z = 0;
      el.push({ type: 'farmhouse', pos: [h2x, getTerrainHeight(h2x, h2z, sceneType), h2z] });
    } else {
      // 梯田环境元素：由于作物使用了 instancedMesh，这里只放置一些地标建筑
      el.push({ type: 'helipad', pos: [0, getTerrainHeight(0, 0, sceneType), 0] });
      
      const hx = 60, hz = 60;
      const hy = getTerrainHeight(hx, hz, sceneType);
      el.push({ type: 'farmhouse', pos: [hx, hy, hz] });
    }

    return el;
  }, [sceneType]);

  const droneFlightPlans = useMemo(() => {
    return droneStarts.map((drone) => {
      const assignedRoutes = routes.filter((route) => route.uavId === drone.id);
      return {
        uavId: drone.id,
        waypoints: [drone.position, ...assignedRoutes.map((route) => route.end)],
      };
    });
  }, [droneStarts, routes]);

  const handleTerrainClick = (e: any) => {
    e.stopPropagation();
    if (page !== 'setup') return;
    if (setupMode === null) return;

    const point = e.point.clone();
    
    if (sceneType === 'terrace') {
      const dx = getTerrainHeight(point.x + 0.1, point.z, sceneType) - point.y;
      const dz = getTerrainHeight(point.x, point.z + 0.1, sceneType) - point.y;
      const slope = Math.sqrt(dx*dx + dz*dz) * 10;
      if (slope > 4) {
        alert("⚠️ 请将无人机起降点设置在平坦的田面上，不要设置在陡峭的田埂边缘！");
        return;
      }
    }
    
    if (setupMode === 'droneStart') {
      const next = [...droneStarts, { id: `UAV-${droneStarts.length + 1}`, position: point }];
      setDroneStarts(next);
      setRoutes([]);
      if (next.length >= droneCount) {
        setSetupMode(null);
      }
    } else if (setupMode === 'taskTarget') {
      const next = [...taskTargets, { id: `TASK-${taskTargets.length + 1}`, position: point }];
      setTaskTargets(next);
      setRoutes([]);
      if (next.length >= taskCount) {
        setSetupMode(null);
      }
    }
  };

  const updateWindLayer = (id: string, field: "speed" | "direction", value: number) => {
    setWindLayers((prev) =>
      prev.map((layer) =>
        layer.id === id
          ? {
              ...layer,
              [field]: field === "direction" ? ((value % 360) + 360) % 360 : Math.max(0, value),
            }
          : layer
      )
    );
  };

  const resetPlanning = () => {
    setDroneStarts([]);
    setTaskTargets([]);
    setRoutes([]);
    setSetupMode(null);
    setDroneTelemetry({});
  };

  const ensureDroneEnergyProfiles = (droneIds: string[]) => {
    setDroneEnergyProfiles((prev) => {
      const next: Record<string, DroneEnergyProfile> = {};
      droneIds.forEach((id) => {
        next[id] = prev[id] ?? initialRouteConfig.energyDefaults;
      });
      return next;
    });
  };

  useEffect(() => {
    ensureDroneEnergyProfiles(droneStarts.map((drone) => drone.id));
  }, [droneStarts]);

  const updateDroneEnergyProfile = (
    uavId: string,
    field: keyof DroneEnergyProfile,
    value: number
  ) => {
    setDroneEnergyProfiles((prev) => {
      const current = prev[uavId] ?? initialRouteConfig.energyDefaults;
      const nextValue =
        field === "initialBatteryPercent"
          ? Math.min(100, Math.max(1, value))
          : field === "baseConsumptionPerMeter"
            ? Math.min(5, Math.max(0.01, value))
            : Math.min(0.2, Math.max(0, value));
      return {
        ...prev,
        [uavId]: {
          ...current,
          [field]: nextValue,
        },
      };
    });
  };

  const autoAssignRoutes = () => {
    if (droneStarts.length === 0 || taskTargets.length === 0) {
      return;
    }

    const workingDrones = droneStarts.map((drone) => ({
      id: drone.id,
      position: drone.position.clone(),
    }));

    const assignedRoutes = taskTargets.map((task, taskIndex) => {
      let bestIndex = 0;
      let bestDistance = Number.POSITIVE_INFINITY;

      workingDrones.forEach((drone, droneIndex) => {
        const distance = drone.position.distanceTo(task.position);
        if (distance < bestDistance) {
          bestDistance = distance;
          bestIndex = droneIndex;
        }
      });

      const selectedDrone = workingDrones[bestIndex];
      const route: RouteConfig = {
        id: `${selectedDrone.id}-${task.id}-${taskIndex + 1}`,
        uavId: selectedDrone.id,
        taskId: task.id,
        start: selectedDrone.position.clone(),
        end: task.position.clone(),
      };

      selectedDrone.position = task.position.clone();
      return route;
    });

    setRoutes(assignedRoutes);
  };

  const seedDroneTelemetry = () => {
    const seeded = Object.fromEntries(
      droneStarts.map((drone) => [
        drone.id,
        {
          batteryPercent: droneEnergyProfiles[drone.id]?.initialBatteryPercent ?? 100,
          consumedPercent: 0,
          baseConsumedPercent: 0,
          windExtraConsumedPercent: 0,
          traveledDistance: 0,
          totalDistance: 0,
          currentWindSpeed: 0,
          isComplete: false,
        } as DroneTelemetry,
      ])
    );
    setDroneTelemetry(seeded);
  };

  const handleDroneTelemetry = useCallback((uavId: string, telemetry: DroneTelemetry) => {
    setDroneTelemetry((prev) => {
      const current = prev[uavId];
      if (
        current &&
        Math.abs(current.batteryPercent - telemetry.batteryPercent) < 0.05 &&
        Math.abs(current.consumedPercent - telemetry.consumedPercent) < 0.05 &&
        Math.abs(current.baseConsumedPercent - telemetry.baseConsumedPercent) < 0.05 &&
        Math.abs(current.windExtraConsumedPercent - telemetry.windExtraConsumedPercent) < 0.05 &&
        Math.abs(current.traveledDistance - telemetry.traveledDistance) < 0.2 &&
        Math.abs(current.totalDistance - telemetry.totalDistance) < 0.2 &&
        Math.abs(current.currentWindSpeed - telemetry.currentWindSpeed) < 0.1 &&
        current.isComplete === telemetry.isComplete
      ) {
        return prev;
      }
      return { ...prev, [uavId]: telemetry };
    });
  }, []);

  const sidePanelStyle: CSSProperties = isCompactLayout
      ? {
        position: 'absolute',
        top: 'auto',
        left: 0,
        right: 0,
        bottom: 0,
        width: '100%',
        height: '280px',
        background: 'rgba(245, 250, 245, 0.96)',
        borderTop: '1px solid rgba(17, 101, 48, 0.35)',
        borderLeft: 'none',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 -10px 30px rgba(0,0,0,0.18)',
      }
    : {
        position: 'absolute',
        top: 0,
        right: 0,
        width: '320px',
        height: '100vh',
        background: 'rgba(245, 250, 245, 0.95)',
        borderLeft: '2px solid #2E8B57',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
      };

  const sidePanelHeaderStyle: CSSProperties = {
    background: '#116530',
    color: 'white',
    padding: isCompactLayout ? '10px 14px' : '20px',
    textAlign: 'center',
    fontSize: isCompactLayout ? '0.95rem' : '1.2rem',
    fontWeight: 'bold',
  };

  const setupPanelContentStyle: CSSProperties = isCompactLayout
    ? {
        padding: '10px',
        flex: 1,
        overflowX: 'hidden',
        overflowY: 'auto',
      }
    : {
        padding: '20px',
        flex: 1,
        overflowY: 'auto',
      };

  const simulationPanelContentStyle: CSSProperties = isCompactLayout
    ? {
        padding: '10px',
        flex: 1,
        overflowX: 'hidden',
        overflowY: 'auto',
      }
    : {
        padding: '20px',
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
      };

  // --- 首页界面 ---
  if (page === 'home') {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        background: isEmbedded
          ? 'radial-gradient(circle at 20% 20%, rgba(16,185,129,0.22), transparent 28%), linear-gradient(135deg, #07130f 0%, #0b261d 52%, #102f43 100%)'
          : 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontFamily: 'Inter, "Noto Sans SC", "Microsoft YaHei", sans-serif',
        boxSizing: 'border-box',
        padding: isEmbedded ? '32px' : 0,
      }}>
        <h1 style={{
          fontSize: isEmbedded ? '2.35rem' : '3rem',
          marginBottom: '10px',
          letterSpacing: 0,
          textShadow: '0 4px 10px rgba(0,0,0,0.3)',
        }}>
          {isEmbedded ? '选择三维作业场景' : '无人机三维仿真平台'}
        </h1>
        <p style={{ fontSize: isEmbedded ? '1rem' : '1.2rem', marginBottom: isEmbedded ? '34px' : '50px', opacity: 0.82 }}>
          路径规划与能耗实验虚拟沙盘
        </p>
        
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', justifyContent: 'center' }}>
          <div 
            onClick={() => enterScene('modern')}
            style={{ width: isEmbedded ? '280px' : '300px', background: 'rgba(255,255,255,0.1)', padding: isEmbedded ? '24px' : '30px', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.3s', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.2)', textAlign: 'center', boxShadow: isEmbedded ? '0 18px 48px rgba(0,0,0,0.2)' : 'none' }}
            onMouseOver={e => e.currentTarget.style.transform = 'translateY(-10px)'}
            onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <div style={{ fontSize: '40px', marginBottom: '15px' }}>🍎</div>
            <h2 style={{ margin: '0 0 10px 0' }}>现代平原果园</h2>
            <p style={{ fontSize: '14px', opacity: 0.7, lineHeight: '1.5' }}>标准的十字形作业道与网格化纺锤形果树种植阵列。</p>
          </div>

          <div 
            onClick={() => enterScene('terrace')}
            style={{ width: isEmbedded ? '280px' : '300px', background: 'rgba(255,255,255,0.1)', padding: isEmbedded ? '24px' : '30px', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.3s', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.2)', textAlign: 'center', boxShadow: isEmbedded ? '0 18px 48px rgba(0,0,0,0.2)' : 'none' }}
            onMouseOver={e => e.currentTarget.style.transform = 'translateY(-10px)'}
            onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <div style={{ fontSize: '40px', marginBottom: '15px' }}>🌾</div>
            <h2 style={{ margin: '0 0 10px 0' }}>高山梯田农场</h2>
            <p style={{ fontSize: '14px', opacity: 0.7, lineHeight: '1.5' }}>极其复杂的垂直海拔落差与密集的农作物覆盖生态。</p>
          </div>
        </div>
      </div>
    );
  }

  // --- 配置与仿真界面 ---
  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#07130f', overflow: 'hidden' }}>
      
      {isEmbedded ? (
        <div
          aria-label="三维场景选择"
          style={{
            position: 'absolute',
            top: isCompactLayout ? '10px' : '18px',
            left: isCompactLayout ? '10px' : '18px',
            zIndex: 20,
            display: 'flex',
            gap: '6px',
            padding: '5px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.18)',
            background: 'rgba(7,19,15,0.78)',
            boxShadow: '0 10px 28px rgba(0,0,0,0.24)',
            backdropFilter: 'blur(12px)',
          }}
        >
          {SCENE_OPTIONS.map((scene) => {
            const active = scene.id === sceneType;
            return (
              <button
                key={scene.id}
                type="button"
                onClick={() => enterScene(scene.id)}
                style={{
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  padding: isCompactLayout ? '7px 9px' : '9px 13px',
                  fontSize: isCompactLayout ? '12px' : '14px',
                  fontWeight: 800,
                  color: active ? '#064e3b' : 'rgba(255,255,255,0.82)',
                  background: active ? '#d1fae5' : 'transparent',
                  boxShadow: active ? '0 0 0 1px rgba(110,231,183,0.35)' : 'none',
                }}
              >
                {scene.icon} {scene.label}
              </button>
            );
          })}
        </div>
      ) : (
        <button
          onClick={() => setPage('home')}
          style={{
            position: 'absolute',
            top: isCompactLayout ? '10px' : '18px',
            left: isCompactLayout ? '10px' : '18px',
            zIndex: 20,
            background: '#1e3c72',
            color: 'white',
            border: 'none',
            padding: isCompactLayout ? '7px 10px' : '10px 18px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            boxShadow: '0 10px 28px rgba(0,0,0,0.24)',
            backdropFilter: 'blur(12px)',
            fontSize: isCompactLayout ? '12px' : '14px',
          }}
        >
          🏠 返回系统首页
        </button>
      )}

      <WindLayerPanel layers={windLayers} onChange={updateWindLayer} compact={isCompactLayout} />

      {page === 'setup' && (
        <>
          {setupMode === 'droneStart' && (
            <div id="instruction-overlay" style={{ position: 'absolute', top: '20px', left: 'calc(50% - 160px)', background: 'rgba(0, 0, 0, 0.7)', color: 'white', padding: '10px 20px', borderRadius: '20px', zIndex: 20 }}>
              请在场景中点击鼠标，设置第 {droneStarts.length + 1} 架无人机的 🟢 起飞点
            </div>
          )}
          {setupMode === 'taskTarget' && (
            <div id="instruction-overlay" style={{ position: 'absolute', top: '20px', left: 'calc(50% - 160px)', background: 'rgba(180, 0, 0, 0.8)', color: 'white', padding: '10px 20px', borderRadius: '20px', zIndex: 20 }}>
              请在场景中点击鼠标，设置第 {taskTargets.length + 1} 个 🔴 任务目标点
            </div>
          )}
          
          <div style={{ position: 'absolute', bottom: isCompactLayout ? '290px' : '20px', left: isCompactLayout ? '10px' : '20px', background: 'rgba(255,255,255,0.9)', padding: isCompactLayout ? '6px 8px' : '10px 15px', borderRadius: '8px', zIndex: 10, fontSize: isCompactLayout ? '10px' : '13px', fontWeight: 'bold' }}>
            🖱️ 左键：旋转视角 | 🖱️ 右键：平移 | 🖱️ 滚轮：缩放
          </div>

          <div id="ui-container" style={sidePanelStyle}>
            <div style={sidePanelHeaderStyle}>
              航线配置中心 ({sceneType === 'modern' ? '平原果园' : '高山梯田'})
            </div>
            <div style={setupPanelContentStyle}>
              <div style={{ background: 'white', borderRadius: '8px', padding: '15px', marginBottom: '20px', border: '1px solid #e0e0e0' }}>
                <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>1. 无人机起点</h3>
                <label style={{ display: 'block', fontSize: '12px', color: '#555', marginBottom: '8px' }}>
                  无人机数量
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={droneCount}
                    onChange={(event) => {
                      const value = Math.max(1, Number(event.target.value));
                      setDroneCount(value);
                      setDroneStarts((prev) => prev.slice(0, value));
                      setRoutes([]);
                    }}
                    style={{ width: '100%', boxSizing: 'border-box', marginTop: '4px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                  />
                </label>
                <button 
                  style={{ width: '100%', background: setupMode === 'droneStart' ? '#28a745' : '#e9ecef', color: setupMode === 'droneStart' ? 'white' : '#333', border: '1px solid #ccc', padding: '10px', borderRadius: '4px', cursor: droneStarts.length >= droneCount ? 'not-allowed' : 'pointer' }}
                  onClick={() => setSetupMode('droneStart')}
                  disabled={setupMode !== null || droneStarts.length >= droneCount}
                >
                  放置无人机起点（{droneStarts.length}/{droneCount}）
                </button>
              </div>

              <div style={{ background: 'white', borderRadius: '8px', padding: '15px', marginBottom: '20px', border: '1px solid #e0e0e0' }}>
                <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>2. 任务目标点</h3>
                <label style={{ display: 'block', fontSize: '12px', color: '#555', marginBottom: '8px' }}>
                  任务数量
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={taskCount}
                    onChange={(event) => {
                      const value = Math.max(1, Number(event.target.value));
                      setTaskCount(value);
                      setTaskTargets((prev) => prev.slice(0, value));
                      setRoutes([]);
                    }}
                    style={{ width: '100%', boxSizing: 'border-box', marginTop: '4px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                  />
                </label>
                <button
                  style={{ width: '100%', background: setupMode === 'taskTarget' ? '#d32f2f' : '#e9ecef', color: setupMode === 'taskTarget' ? 'white' : '#333', border: '1px solid #ccc', padding: '10px', borderRadius: '4px', cursor: taskTargets.length >= taskCount ? 'not-allowed' : 'pointer' }}
                  onClick={() => setSetupMode('taskTarget')}
                  disabled={setupMode !== null || taskTargets.length >= taskCount}
                >
                  放置任务目标（{taskTargets.length}/{taskCount}）
                </button>
              </div>

              <div style={{ background: 'white', borderRadius: '8px', padding: '15px', marginBottom: '20px', border: '1px solid #e0e0e0' }}>
                <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>3. 自动匹配</h3>
                <button
                  style={{ width: '100%', background: '#116530', color: 'white', border: 'none', padding: '10px', borderRadius: '4px', cursor: droneStarts.length === 0 || taskTargets.length === 0 ? 'not-allowed' : 'pointer', opacity: droneStarts.length === 0 || taskTargets.length === 0 ? 0.5 : 1 }}
                  onClick={autoAssignRoutes}
                  disabled={droneStarts.length === 0 || taskTargets.length === 0}
                >
                  根据最近距离自动匹配任务
                </button>
                <button
                  style={{ width: '100%', marginTop: '8px', background: '#fff0f0', color: '#dc3545', border: '1px solid #dc3545', padding: '9px', borderRadius: '4px', cursor: 'pointer' }}
                  onClick={resetPlanning}
                >
                  清空重新设置
                </button>
              </div>

              {droneStarts.length > 0 && (
                <div style={{ background: 'white', borderRadius: '8px', padding: '15px', marginBottom: '20px', border: '1px solid #e0e0e0' }}>
                  <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>4. 每机能耗参数</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '300px', overflowY: 'auto' }}>
                    {droneStarts.map((drone) => {
                      const profile = droneEnergyProfiles[drone.id] ?? {
                        initialBatteryPercent: 100,
                        baseConsumptionPerMeter: 0.035,
                        windSensitivity: 0.0015,
                      };
                      return (
                        <div key={drone.id} style={{ background: '#f8f9fa', borderRadius: '6px', padding: '10px', borderLeft: '4px solid #4CAF50' }}>
                          <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '8px' }}>🛸 {drone.id}</div>
                          <label style={{ display: 'block', fontSize: '11px', color: '#555', marginBottom: '6px' }}>
                            初始电量（%）
                            <input
                              type="number"
                              min="1"
                              max="100"
                              step="1"
                              value={profile.initialBatteryPercent}
                              onChange={(event) => updateDroneEnergyProfile(drone.id, "initialBatteryPercent", Number(event.target.value))}
                              style={{ width: '100%', boxSizing: 'border-box', marginTop: '3px', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                            />
                          </label>
                          <label style={{ display: 'block', fontSize: '11px', color: '#555', marginBottom: '6px' }}>
                            基础耗电（%/m）
                            <input
                              type="number"
                              min="0.01"
                              max="5"
                              step="0.01"
                              value={profile.baseConsumptionPerMeter}
                              onChange={(event) => updateDroneEnergyProfile(drone.id, "baseConsumptionPerMeter", Number(event.target.value))}
                              style={{ width: '100%', boxSizing: 'border-box', marginTop: '3px', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                            />
                          </label>
                          <label style={{ display: 'block', fontSize: '11px', color: '#555' }}>
                            风敏感系数
                            <input
                              type="number"
                              min="0"
                              max="0.2"
                              step="0.0001"
                              value={profile.windSensitivity}
                              onChange={(event) => updateDroneEnergyProfile(drone.id, "windSensitivity", Number(event.target.value))}
                              style={{ width: '100%', boxSizing: 'border-box', marginTop: '3px', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                            />
                          </label>
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ fontSize: '11px', color: '#666', lineHeight: 1.5, marginTop: '8px' }}>
                    已按 UAV_datas 实测区间标定默认值：基础耗电约 0.035 %/m（可调），风耗采用逆风增益。
                  </div>
                </div>
              )}

              {(droneStarts.length > 0 || taskTargets.length > 0) && (
                <div style={{ background: 'white', borderRadius: '8px', padding: '15px', marginBottom: '20px', border: '1px solid #e0e0e0' }}>
                  <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>已设置点位</h3>
                  <div style={{ fontSize: '12px', color: '#444', lineHeight: 1.7 }}>
                    无人机起点：{droneStarts.length}/{droneCount}<br />
                    任务目标点：{taskTargets.length}/{taskCount}
                  </div>
                </div>
              )}

              {routes.length > 0 && (
                <div style={{ background: 'white', borderRadius: '8px', padding: '15px', border: '1px solid #e0e0e0' }}>
                  <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>📋 自动匹配航线 ({routes.length})</h3>
                  <div style={{ maxHeight: '300px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {routes.map((r) => (
                      <div key={r.id} style={{ background: '#e3f2fd', padding: '10px', borderRadius: '6px', borderLeft: '4px solid #2196F3' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <strong style={{fontSize: '12px'}}>{r.uavId} → {r.taskId}</strong>
                          <button onClick={() => setRoutes(routes.filter(route => route.id !== r.id))} style={{ background: 'none', border: 'none', color: '#f44336', cursor: 'pointer', fontWeight: 'bold' }}>✖</button>
                        </div>
                        <div style={{ fontSize: '11px', color: '#555' }}>
                          起点: [{r.start.x.toFixed(1)}, {r.start.z.toFixed(1)}] <br/>
                          任务: [{r.end.x.toFixed(1)}, {r.end.z.toFixed(1)}]
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button 
                style={{ width: '100%', marginTop: '20px', background: '#28a745', color: 'white', border: 'none', padding: '12px', fontSize: '16px', fontWeight: 'bold', borderRadius: '4px', cursor: routes.length === 0 ? 'not-allowed' : 'pointer', opacity: routes.length === 0 ? 0.5 : 1 }}
                onClick={() => {
                  if (routes.length === 0) return;
                  setSetupMode(null);
                  seedDroneTelemetry();
                  setPage('simulation');
                }}
                disabled={routes.length === 0}
              >
                 前往仿真界面 ➡️
              </button>
            </div>
          </div>
        </>
      )}

      {page === 'simulation' && (
        <>
          <div style={{ position: 'absolute', top: isCompactLayout ? '52px' : '315px', left: isCompactLayout ? '170px' : '20px', background: 'rgba(17, 101, 48, 0.9)', color: 'white', padding: isCompactLayout ? '7px 10px' : '10px 20px', borderRadius: '8px', zIndex: 10, fontSize: isCompactLayout ? '12px' : '16px', fontWeight: 'bold' }}>
            🔴 正在仿真模拟中...
          </div>

          <div style={sidePanelStyle}>
            <div style={sidePanelHeaderStyle}>
              无人机实时监控
            </div>
            <div style={simulationPanelContentStyle}>
              <div style={{ background: 'white', borderRadius: '8px', padding: '15px', flex: 1, overflowY: 'auto' }}>
                <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>📊 任务执行列表</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {droneFlightPlans.map((plan) => {
                    const profile = droneEnergyProfiles[plan.uavId] ?? {
                      initialBatteryPercent: 100,
                      baseConsumptionPerMeter: 0.035,
                      windSensitivity: 0.0015,
                    };
                    const telemetry = droneTelemetry[plan.uavId] ?? {
                      batteryPercent: profile.initialBatteryPercent,
                      consumedPercent: 0,
                      baseConsumedPercent: 0,
                      windExtraConsumedPercent: 0,
                      traveledDistance: 0,
                      totalDistance: 0,
                      currentWindSpeed: 0,
                      isComplete: false,
                    };
                    const progressPercent = telemetry.totalDistance > 0
                      ? Math.min((telemetry.traveledDistance / telemetry.totalDistance) * 100, 100)
                      : 0;
                    const batteryColor = telemetry.batteryPercent > 50 ? '#2e7d32' : telemetry.batteryPercent > 20 ? '#f9a825' : '#c62828';
                    return (
                      <div key={plan.uavId} style={{ background: '#f5f7f8', padding: '12px', borderRadius: '6px', borderLeft: `4px solid ${batteryColor}` }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <strong style={{ fontSize: '13px' }}>🛸 {plan.uavId}</strong>
                          <span style={{ color: batteryColor, fontWeight: 'bold', fontSize: '12px' }}>
                            {telemetry.batteryPercent.toFixed(1)}%
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: '#444', lineHeight: 1.5 }}>
                          <div>已损耗：{telemetry.consumedPercent.toFixed(1)}%</div>
                          <div>基础损耗：{telemetry.baseConsumedPercent.toFixed(1)}%</div>
                          <div>风场附加：{telemetry.windExtraConsumedPercent.toFixed(1)}%</div>
                          <div>飞行进度：{progressPercent.toFixed(1)}%</div>
                          <div>飞行距离：{telemetry.traveledDistance.toFixed(1)} / {telemetry.totalDistance.toFixed(1)} m</div>
                          <div>当前风速：{telemetry.currentWindSpeed.toFixed(1)} m/s</div>
                        </div>
                        <div style={{ marginTop: '8px', height: '8px', borderRadius: '999px', background: '#dde3e8', overflow: 'hidden' }}>
                          <div style={{ width: `${telemetry.batteryPercent}%`, height: '100%', background: batteryColor, transition: 'width 0.15s linear' }} />
                        </div>
                        {telemetry.batteryPercent <= 20 && (
                          <div style={{ marginTop: '6px', fontSize: '11px', color: '#c62828', fontWeight: 'bold' }}>
                            ⚠️ 电量低，请尽快返航
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {routes.map((r) => (
                    <div key={r.id} style={{ background: '#f8f9fa', padding: '12px', borderRadius: '6px', borderLeft: '4px solid #4CAF50' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <strong style={{ fontSize: '13px' }}>🛸 {r.uavId} → {r.taskId}</strong>
                        <span style={{ color: '#4CAF50', fontWeight: 'bold', fontSize: '11px', background: '#c8e6c9', padding: '2px 6px', borderRadius: '4px' }}>飞行中</span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#444', lineHeight: '1.5' }}>
                        <div>🟢 起点：[{r.start.x.toFixed(1)}, {r.start.z.toFixed(1)}]</div>
                        <div>🔴 任务：[{r.end.x.toFixed(1)}, {r.end.z.toFixed(1)}]</div>
                        <div style={{ color: '#666', marginTop: '4px' }}>
                          高程: {r.start.y.toFixed(1)}m ➡️ {r.end.y.toFixed(1)}m
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <button 
                style={{ width: '100%', marginTop: '15px', padding: '12px', background: '#fff0f0', color: '#dc3545', border: '1px solid #dc3545', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                onClick={() => setPage('setup')}
              >
                🔙 结束仿真并返回
              </button>
            </div>
          </div>
        </>
      )}

      {/* 3D 渲染区 */}
      <Canvas shadows camera={{ position: [-100, 150, 180], fov: 40 }}>
        <Sky sunPosition={[100, 30, 100]} turbidity={0.5} rayleigh={2} mieCoefficient={0.005} />
        <ambientLight intensity={0.4} />
        <directionalLight 
          castShadow position={[80, 150, 80]} intensity={1.3} 
          shadow-mapSize={[4096, 4096]}
          shadow-camera-left={-200} shadow-camera-right={200}
          shadow-camera-top={200} shadow-camera-bottom={-200}
          shadow-camera-near={0.5} shadow-camera-far={500}
          shadow-bias={-0.0005}
        />
        
        <Terrain sceneType={sceneType} onPointerDown={handleTerrainClick} />

        <WindLayerVisualization layers={windLayers} />
        
        {/* 利用 InstancedMesh 高性能渲染水稻田生态 */}
        <CropInstanced count={16000} type={sceneType} />

        {elements.map((el, index) => {
          if (el.type === 'apple') return <ModernAppleTree key={index} position={el.pos} />;
          if (el.type === 'poplar') return <PoplarTree key={index} position={el.pos} />;
          if (el.type === 'helipad') return <Helipad key={index} position={el.pos} />;
          if (el.type === 'farmhouse') return <FarmHouse key={index} position={el.pos} />;
          return null;
        })}
        
        {droneStarts.map((drone) => (
          <Marker key={drone.id} position={drone.position} type="start" />
        ))}

        {taskTargets.map((task) => (
          <Marker key={task.id} position={task.position} type="end" />
        ))}

        {droneFlightPlans.map((plan) => (
          <MultiLegDrone
            key={plan.uavId}
            uavId={plan.uavId}
            waypoints={plan.waypoints}
            isSimulating={page === 'simulation'}
            sceneType={sceneType}
            energyProfile={droneEnergyProfiles[plan.uavId] ?? {
              initialBatteryPercent: 100,
              baseConsumptionPerMeter: 0.035,
              windSensitivity: 0.0015,
            }}
            windLayers={windLayers}
            onTelemetry={handleDroneTelemetry}
          />
        ))}
        
        <OrbitControls 
          makeDefault 
          target={[0, sceneType === 'terrace' ? 78 : 25, 0]}
          maxPolarAngle={Math.PI / 2 - 0.05} 
          autoRotate={page === 'setup' && setupMode === null} 
          autoRotateSpeed={0.2}
          minDistance={20} maxDistance={400}
        />
      </Canvas>
    </div>
  );
}
