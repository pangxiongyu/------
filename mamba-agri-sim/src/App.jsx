import { lazy, Suspense } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Navbar from './components/common/Navbar'

const HomePage = lazy(() => import('./pages/HomePage'))
const SceneDetailPage = lazy(() => import('./pages/SceneDetailPage'))
const ApplicationsPage = lazy(() => import('./pages/ApplicationsPage'))
const FlightParamsPage = lazy(() => import('./pages/FlightParamsPage'))
const Viewport3DPage = lazy(() => import('./pages/Viewport3DPage'))
const DataDisplayPage = lazy(() => import('./pages/DataDisplayPage'))
const TransitionPage = lazy(() => import('./pages/TransitionPage'))
const ThanksPage = lazy(() => import('./pages/ThanksPage'))

function LoadingFallback() {
  return (
    <div className="min-h-screen pt-16 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-[3px] border-agri-200 border-t-agri-500 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">加载中...</p>
      </div>
    </div>
  )
}

export default function App() {
  const location = useLocation()

  return (
    <>
      <Navbar />
      <Suspense fallback={<LoadingFallback />}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<HomePage />} />
            <Route path="/scene-detail" element={<SceneDetailPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/flight-params" element={<FlightParamsPage />} />
            <Route path="/viewport-3d" element={<Viewport3DPage />} />
            <Route path="/data-display" element={<DataDisplayPage />} />
            <Route path="/transition" element={<TransitionPage />} />
            <Route path="/thanks" element={<ThanksPage />} />
          </Routes>
        </AnimatePresence>
      </Suspense>
    </>
  )
}
