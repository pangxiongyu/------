import { createContext, useContext, useState, useEffect } from 'react';
const AuthContext = createContext();
const storagekey = 'mamba_agri_sim_users';
const currentuserkey = 'mamba_agri_sim_current_user';
function loadusers() {
  try {
    const raw = localStorage.getItem(storagekey);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}
function saveusers(users) {
  localStorage.setItem(storagekey, JSON.stringify(users));
}
function loadcurrentuser() {
  try {
    const raw = localStorage.getItem(currentuserkey);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
function savecurrentuser(user) {
  if (user) {
    localStorage.setItem(currentuserkey, JSON.stringify(user));
  } else {
    localStorage.removeItem(currentuserkey);
  }
}
export function AuthProvider({
  children
}) {
  const [user, setuser] = useState(() => loadcurrentuser());
  useEffect(() => {
    savecurrentuser(user);
  }, [user]);
  function login(username, password) {
    const users = loadusers();
    const stored = users[username];
    if (!stored) {
      return {
        ok: false,
        error: '用户不存在，请先注册'
      };
    }
    if (stored.password !== password) {
      return {
        ok: false,
        error: '密码错误'
      };
    }
    setuser({
      username,
      displayName: stored.displayName
    });
    return {
      ok: true
    };
  }
  function register(username, password, displayname) {
    if (!username || !password || !displayname) {
      return {
        ok: false,
        error: '请填写所有字段'
      };
    }
    if (username.length < 3 || username.length > 20) {
      return {
        ok: false,
        error: '用户名需 3-20 个字符'
      };
    }
    if (password.length < 6) {
      return {
        ok: false,
        error: '密码至少 6 位'
      };
    }
    const users = loadusers();
    if (users[username]) {
      return {
        ok: false,
        error: '用户名已存在'
      };
    }
    users[username] = {
      password,
      displayName: displayname
    };
    saveusers(users);
    setuser({
      username,
      displayName: displayname
    });
    return {
      ok: true
    };
  }
  function logout() {
    setuser(null);
  }
  return <AuthContext.Provider value={{
    user,
    login,
    register,
    logout
  }}>
      {children}
    </AuthContext.Provider>;
}
function useauth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
export { useauth };
