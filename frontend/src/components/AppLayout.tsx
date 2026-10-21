import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { useAuth } from '../context/AuthContext'

interface AppLayoutProps {
  children: React.ReactNode
  title?: string
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children, title }) => {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar onLogout={handleLogout} />

      {/* Main Content */}
      <main className="md:ml-64 min-h-screen">
        {/* Topbar */}
        <Topbar />

        {/* Page Content */}
        <div className="pt-24 pb-8 px-4 md:px-8">
          {title && (
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{title}</h1>
            </div>
          )}
          {children}
        </div>
      </main>
    </div>
  )
}
