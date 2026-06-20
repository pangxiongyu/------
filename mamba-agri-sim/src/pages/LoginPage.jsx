import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import PageContainer from '../components/common/PageContainer'
import { HiUser, HiLockClosed, HiArrowRight, HiLogin } from 'react-icons/hi'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    const result = login(username, password)
    if (result.ok) {
      navigate('/')
    } else {
      setError(result.error)
    }
  }

  return (
    <PageContainer>
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-agri-50 via-white to-emerald-50" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-agri-100/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-emerald-100/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/4" />

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative w-full max-w-md"
        >
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white shadow-lg shadow-agri-200 mb-4 overflow-hidden">
              <img src="/brand-logo.svg" alt="智翼农航" className="w-16 h-16" />
            </div>
            <h2 className="text-2xl font-black text-dark">登录智翼农航</h2>
            <p className="text-gray-400 text-sm mt-1">智慧农业无人机协同系统</p>
          </div>

          {/* Form card */}
          <div className="glass-card-premium p-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-600 mb-2">用户名</label>
                <div className="relative">
                  <HiUser className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="请输入用户名"
                    className="input-glow pl-11"
                    autoFocus
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-600 mb-2">密码</label>
                <div className="relative">
                  <HiLockClosed className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                    className="input-glow pl-11"
                  />
                </div>
              </div>

              {error && (
                <motion.p
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-red-500 bg-red-50 rounded-xl px-4 py-2.5"
                >
                  {error}
                </motion.p>
              )}

              <button
                type="submit"
                className="btn-primary w-full justify-center text-base py-3.5 bg-gradient-to-r from-agri-500 to-emerald-600 shadow-glow-sm hover:shadow-glow group"
              >
                <HiLogin className="w-5 h-5" />
                登 录
                <HiArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
              </button>
            </form>
          </div>

          <p className="text-center mt-6 text-sm text-gray-400">
            还没有账号？{' '}
            <Link to="/register" className="text-agri-600 font-semibold hover:text-agri-700 transition-colors">
              立即注册
            </Link>
          </p>
        </motion.div>
      </div>
    </PageContainer>
  )
}
