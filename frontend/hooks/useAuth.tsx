'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { authAPI } from '@/services/api'
import { User } from '@/services/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (idToken: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      authAPI.getMe()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (idToken: string) => {
    try {
      const response = await authAPI.login(idToken)
      localStorage.setItem('access_token', response.access_token)
      
      const userData = await authAPI.getMe()
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      try {
        const { logoutFromFirebase } = await import('@/services/firebase')
        await logoutFromFirebase()
      } catch (error) {
        console.error('Firebase sign-out error:', error)
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
