import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '../services/api'
import type { UserResponse, Token } from '../types/api'

interface AuthContextType {
  user: UserResponse | null
  loading: boolean
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

interface RegisterData {
  email: string
  password: string
  full_name: string
  phone?: string
  preferred_language: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    initAuth()
  }, [])

  const initAuth = async () => {
    const token = localStorage.getItem('access_token')
    const refreshToken = localStorage.getItem('refresh_token')

    if (token && refreshToken) {
      api.setTokens(token, refreshToken)
      try {
        await refreshUser()
      } catch {
        await logout()
      }
    }
    setLoading(false)
  }

  const refreshUser = async () => {
    try {
      const userData = await api.getCurrentUser()
      setUser(userData)
    } catch {
      throw new Error('Failed to refresh user')
    }
  }

  const login = async (email: string, password: string, rememberMe = false) => {
    const tokens = await api.login(email, password)
    api.setTokens(tokens.access_token, tokens.refresh_token)
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    if (rememberMe) {
      localStorage.setItem('remember_me', 'true')
    }
    await refreshUser()
  }

  const register = async (data: RegisterData) => {
    await api.register(data)
    // Auto-login after registration
    await login(data.email, data.password)
  }

  const logout = async () => {
    try {
      await api.logout()
    } catch {
      // Ignore logout errors
    } finally {
      api.clearTokens()
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('remember_me')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}