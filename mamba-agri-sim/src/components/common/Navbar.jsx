import { useState, useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { HiSearch, HiMenu, HiX, HiUser, HiLogin, HiLogout, HiUserAdd } from 'react-icons/hi'
import { NAV_ITEMS } from '../../data/navItems'
import { useAuth } from '../../context/AuthContext'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Close dropdown on click outside
  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  useEffect(() => { setMobileOpen(false) }, [location])

  const isHome = location.pathname === '/'
  const isImmersive3D = location.pathname === '/viewport-3d'
  const bgClass = scrolled || !isHome
    ? isImmersive3D
      ? 'bg-[#07130f]/92 backdrop-blur-xl border-b border-white/10 shadow-none'
      : 'bg-white/90 backdrop-blur-xl shadow-sm border-b border-gray-100/60'
    : 'bg-transparent'

  const handleLogout = () => {
    logout()
    setMenuOpen(false)
    navigate('/')
  }

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${bgClass}`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-300 overflow-hidden">
              <img src="/brand-logo.svg" alt="智翼农航" className="w-9 h-9" />
            </div>
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-white animate-breathe" />
          </div>
          <span className={`text-lg font-bold transition-colors ${
            isImmersive3D
              ? 'text-white group-hover:text-agri-200'
              : 'text-dark group-hover:text-agri-600'
          }`}>
            智翼<span className="text-agri-500">农航</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname === item.path
            const navLinkClass = isImmersive3D
              ? active
                ? 'text-white bg-white/10'
                : 'text-white/70 hover:text-white hover:bg-white/10'
              : active
                ? 'text-agri-700 bg-agri-50/80'
                : 'text-gray-600 hover:text-agri-600 hover:bg-gray-50/80'
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${navLinkClass}`}
              >
                {item.label}
                {active && (
                  <span className={`absolute bottom-1 left-1/2 -translate-x-1/2 w-5 h-[2px] rounded-full bg-gradient-to-r ${
                    isImmersive3D ? 'from-agri-300 to-emerald-200' : 'from-agri-400 to-agri-600'
                  }`} />
                )}
              </Link>
            )
          })}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          <div className={`hidden sm:flex items-center gap-2 rounded-xl px-3.5 py-2.5 backdrop-blur-sm transition-all duration-300 focus-within:border-agri-300 focus-within:shadow-glow-sm ${
            isImmersive3D
              ? 'bg-white/10 border border-white/10'
              : 'bg-gray-100/80 border border-gray-200/60'
          }`}>
            <HiSearch className={`${isImmersive3D ? 'text-white/50' : 'text-gray-400'} w-4 h-4 flex-shrink-0`} />
            <input
              type="text"
              placeholder="搜索..."
              className={`bg-transparent text-sm outline-none w-28 ${
                isImmersive3D
                  ? 'text-white placeholder:text-white/45'
                  : 'text-gray-600 placeholder:text-gray-400'
              }`}
            />
          </div>

          {/* User area */}
          {user ? (
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gradient-to-r from-agri-50 to-emerald-50 border border-agri-100/60 hover:border-agri-200 transition-all duration-200 cursor-pointer"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-agri-500 to-agri-700 flex items-center justify-center text-white text-sm font-bold shadow-sm">
                  {user.displayName.charAt(0)}
                </div>
                <span className="text-sm font-semibold text-dark hidden sm:block">{user.displayName}</span>
                <svg className={`w-3 h-3 text-gray-400 transition-transform duration-200 ${menuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {menuOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-white/95 backdrop-blur-xl rounded-xl border border-gray-100 shadow-xl shadow-gray-200/50 py-2 animate-fade-in-up">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-bold text-dark">{user.displayName}</p>
                    <p className="text-xs text-gray-400">@{user.username}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-600 hover:text-red-500 hover:bg-red-50 transition-colors"
                  >
                    <HiLogout className="w-4 h-4" />
                    退出登录
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="hidden sm:flex items-center gap-2">
              <Link
                to="/login"
                className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                  isImmersive3D
                    ? 'text-agri-200 hover:bg-white/10'
                    : 'text-agri-600 hover:bg-agri-50'
                }`}
              >
                <HiLogin className="w-4 h-4" />
                登录
              </Link>
              <Link
                to="/register"
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-agri-500 to-emerald-600 hover:shadow-glow-sm transition-all"
              >
                <HiUserAdd className="w-4 h-4" />
                注册
              </Link>
            </div>
          )}

          <button
            className={`lg:hidden p-2 rounded-lg transition-colors ${
              isImmersive3D
                ? 'text-white/80 hover:bg-white/10'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <HiX className="w-6 h-6" /> : <HiMenu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className={`lg:hidden backdrop-blur-xl border-t shadow-lg ${
          isImmersive3D
            ? 'bg-[#07130f]/95 border-white/10'
            : 'bg-white/95 border-gray-100'
        }`}>
          <div className="px-4 py-3 flex flex-col gap-1">
            {NAV_ITEMS.map((item) => {
              const active = location.pathname === item.path
              const mobileLinkClass = isImmersive3D
                ? active
                  ? 'bg-white/10 text-white'
                  : 'text-white/70 hover:bg-white/10'
                : active
                  ? 'bg-agri-50 text-agri-700 shadow-sm'
                  : 'text-gray-600 hover:bg-gray-50'
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${mobileLinkClass}`}
                >
                  {item.label}
                </Link>
              )
            })}

            {/* Mobile auth links */}
            <div className={`border-t pt-2 mt-2 ${isImmersive3D ? 'border-white/10' : 'border-gray-100'}`}>
              {user ? (
                <>
                  <div className="px-4 py-2 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-agri-500 to-agri-700 flex items-center justify-center text-white font-bold text-sm">
                      {user.displayName.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-dark">{user.displayName}</p>
                      <p className="text-xs text-gray-400">@{user.username}</p>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-red-500 hover:bg-red-50 transition-all"
                  >
                    <HiLogout className="w-4 h-4" />
                    退出登录
                  </button>
                </>
              ) : (
                <div className="flex gap-2 px-4">
                  <Link to="/login" className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-agri-600 bg-agri-50 hover:bg-agri-100 transition-all">
                    <HiLogin className="w-4 h-4" />
                    登录
                  </Link>
                  <Link to="/register" className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-agri-500 to-emerald-600 transition-all">
                    <HiUserAdd className="w-4 h-4" />
                    注册
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
