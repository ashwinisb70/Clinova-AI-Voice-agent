import React, { createContext, useState, useEffect } from 'react'

export interface User {
  username: string
  role: 'admin' | 'staff' | 'patient'
  hospital_id: string
  display_name?: string
}

interface AuthContextType {
  authToken: string | null
  user: User | null
  isLoading: boolean
  login: (token: string, user: User) => void
  logout: () => void
  setUser: (user: User | null) => void
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authToken, setAuthToken] = useState<string | null>(null)
  const [user, setUserState] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load token from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('authToken')
    const userStr = localStorage.getItem('user')
    
    if (token && userStr) {
      try {
        const parsedUser = JSON.parse(userStr)
        setAuthToken(token)
        setUserState(parsedUser)
      } catch (e) {
        console.error('Failed to parse user from localStorage', e)
        logout()
      }
    }
    setIsLoading(false)
  }, [])

  const login = (token: string, userData: User) => {
    localStorage.setItem('authToken', token)
    localStorage.setItem('user', JSON.stringify(userData))
    setAuthToken(token)
    setUserState(userData)
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('user')
    setAuthToken(null)
    setUserState(null)
  }

  const setUser = (userData: User | null) => {
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData))
    } else {
      localStorage.removeItem('user')
    }
    setUserState(userData)
  }

  return (
    <AuthContext.Provider value={{ authToken, user, isLoading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = React.useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
