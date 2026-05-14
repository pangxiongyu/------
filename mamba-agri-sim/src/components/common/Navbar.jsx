import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { HiSearch, HiMenu, HiX } from 'react-icons/hi'
import { NAV_ITEMS } from '../../data/navItems'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => { setMobileOpen(false) }, [location])

  const isHome = location.pathname === '/'
  const bgClass = scrolled || !isHome
    ? 'bg-white/90 backdrop-blur-xl shadow-sm border-b border-gray-100/60'
    : 'bg-transparent'

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${bgClass}`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-agri-500 to-agri-700 flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-300">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L2 19h6l4-8 4 8h6L12 2z"/>
                <circle cx="12" cy="19" r="2"/>
              </svg>
            </div>
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-white animate-breathe" />
          </div>
          <span className="text-lg font-bold text-dark group-hover:text-agri-600 transition-colors">
            智农<span className="text-agri-500">Mamba</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  active
                    ? 'text-agri-700 bg-agri-50/80'
                    : 'text-gray-600 hover:text-agri-600 hover:bg-gray-50/80'
                }`}
              >
                {item.label}
                {active && (
                  <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-5 h-[2px] rounded-full bg-gradient-to-r from-agri-400 to-agri-600" />
                )}
              </Link>
            )
          })}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 bg-gray-100/80 backdrop-blur-sm rounded-xl px-3.5 py-2.5 border border-gray-200/60 transition-all duration-300 focus-within:border-agri-300 focus-within:shadow-glow-sm">
            <HiSearch className="text-gray-400 w-4 h-4 flex-shrink-0" />
            <input
              type="text"
              placeholder="搜索..."
              className="bg-transparent text-sm text-gray-600 outline-none w-28 placeholder:text-gray-400"
            />
          </div>
          <button className="relative flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-br from-agri-500 to-agri-600 text-white text-xs font-bold shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
            <span className="relative z-10">登</span>
          </button>
          <button
            className="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <HiX className="w-6 h-6" /> : <HiMenu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="lg:hidden bg-white/95 backdrop-blur-xl border-t border-gray-100 shadow-lg">
          <div className="px-4 py-3 flex flex-col gap-1">
            {NAV_ITEMS.map((item) => {
              const active = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    active
                      ? 'bg-agri-50 text-agri-700 shadow-sm'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </nav>
  )
}
