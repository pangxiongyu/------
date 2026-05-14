import PageContainer from '../components/common/PageContainer'
import TerrainScene from '../components/viewport-3d/TerrainScene'
import UAVControlPanel from '../components/viewport-3d/UAVControlPanel'

export default function Viewport3DPage() {
  return (
    <PageContainer>
      <div className="h-[calc(100vh-4rem)] flex flex-col lg:flex-row gap-4 p-4">
        {/* 3D canvas - takes most space */}
        <div className="flex-1 min-h-0">
          <TerrainScene />
        </div>
        {/* Right panel */}
        <div className="w-full lg:w-80 flex-shrink-0">
          <UAVControlPanel />
        </div>
      </div>
    </PageContainer>
  )
}
