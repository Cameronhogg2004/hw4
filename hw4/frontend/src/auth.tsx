import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import * as api from './api'

const TOKEN_KEY = 'cc_token'

interface AuthState {
  user: api.User | null
  token: string | null
  ready: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (data: { first_name: string; last_name: string; email: string; password: string }) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<api.User | null>(null)
  const [ready, setReady] = useState(false)

  // On load, turn a saved token back into a user (or drop it if it expired).
  useEffect(() => {
    if (!token) {
      setReady(true)
      return
    }
    api
      .fetchMe(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
      })
      .finally(() => setReady(true))
    // Only on first mount; login/signup set user directly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const accept = useCallback((res: api.AuthResponse) => {
    localStorage.setItem(TOKEN_KEY, res.token)
    setToken(res.token)
    setUser(res.user)
  }, [])

  const value: AuthState = {
    user,
    token: user ? token : null,
    ready,
    login: async (email, password) => accept(await api.login(email, password)),
    signup: async (data) => accept(await api.signup(data)),
    logout: async () => {
      if (token) await api.logout(token).catch(() => undefined)
      localStorage.removeItem(TOKEN_KEY)
      setToken(null)
      setUser(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
