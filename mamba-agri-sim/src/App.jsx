import { lazy, Suspense } from 'react'
import { Routes, Route, useLocation, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Navbar from './components/common/Navbar'
import { useAuth } from './context/AuthContext'

const HomePage = lazy(() => import('./pages/HomePage'))
const SceneDetailPage = lazy(() => import('./pages/SceneDetailPage'))
const ApplicationsPage = lazy(() => import('./pages/ApplicationsPage'))
const FlightParamsPage = lazy(() => import('./pages/FlightParamsPage'))
const Viewport3DPage = lazy(() => import('./pages/Viewport3DPage'))
const DataDisplayPage = lazy(() => import('./pages/DataDisplayPage'))
const TransitionPage = lazy(() => import('./pages/TransitionPage'))
const ThanksPage = lazy(() => import('./pages/ThanksPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))

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
  const { user } = useAuth()

  const hideNav = location.pathname === '/login' || location.pathname === '/register'

  return (
    <>
      {!hideNav && <Navbar />}
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
            <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
            <Route path="/register" element={user ? <Navigate to="/" replace /> : <RegisterPage />} />
          </Routes>
        </AnimatePresence>
      </Suspense>
    </>
  )
}
