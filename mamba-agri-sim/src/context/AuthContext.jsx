import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

const STORAGE_KEY = 'mamba_agri_sim_users'
const CURRENT_USER_KEY = 'mamba_agri_sim_current_user'

function loadUsers() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveUsers(users) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users))
}

function loadCurrentUser() {
  try {
    const raw = localStorage.getItem(CURRENT_USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveCurrentUser(user) {
  if (user) {
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user))
  } else {
    localStorage.removeItem(CURRENT_USER_KEY)
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => loadCurrentUser())

  useEffect(() => {
    saveCurrentUser(user)
  }, [user])

  function login(username, password) {
    const users = loadUsers()
    const stored = users[username]
    if (!stored) {
      return { ok: false, error: '用户不存在，请先注册' }
    }
    if (stored.password !== password) {
      return { ok: false, error: '密码错误' }
    }
    setUser({ username, displayName: stored.displayName })
    return { ok: true }
  }

  function register(username, password, displayName) {
    if (!username || !password || !displayName) {
      return { ok: false, error: '请填写所有字段' }
    }
    if (username.length < 3 || username.length > 20) {
      return { ok: false, error: '用户名需 3-20 个字符' }
    }
    if (password.length < 6) {
      return { ok: false, error: '密码至少 6 位' }
    }
    const users = loadUsers()
    if (users[username]) {
      return { ok: false, error: '用户名已存在' }
    }
    users[username] = { password, displayName }
    saveUsers(users)
    setUser({ username, displayName })
    return { ok: true }
  }

  function logout() {
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
