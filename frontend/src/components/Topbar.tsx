import React, { useState } from 'react'
import { Bell, Search, ChevronDown, Globe, Moon, Sun } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'
import { useTheme } from '../context/ThemeContext'
import { Link, useNavigate } from 'react-router-dom'

interface TopbarProps {
  onSearch?: (query: string) => void
}

export const Topbar: React.FC<TopbarProps> = ({ onSearch }) => {
  const { user } = useAuth()
  const { language, setLanguage } = useLanguage()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [showLanguageMenu, setShowLanguageMenu] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)
    onSearch?.(query)
  }

  return (
    <div className="fixed top-0 right-0 left-0 md:left-64 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 z-30 h-16 flex items-center px-6">
      <div className="flex items-center justify-between w-full">
        {/* Search Box */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" size={20} />
            <input
              type="text"
              placeholder="Search anything..."
              value={searchQuery}
              onChange={handleSearch}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 bg-gray-50 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-6 ml-auto">
          {/* Notifications */}
          <button
            onClick={() => navigate('/notifications')}
            className="relative text-gray-600 hover:text-gray-900 transition-colors dark:text-gray-400 dark:hover:text-gray-200"
            title="View notifications"
          >
            <Bell size={24} />
            <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="flex items-center justify-center w-10 h-10 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </button>

          {/* Language Selector */}
          <div className="relative">
            <button
              onClick={() => setShowLanguageMenu(!showLanguageMenu)}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors px-3 py-2 rounded-lg hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
              title="Change language"
            >
              <Globe size={20} />
              <span className="text-sm font-medium uppercase">{language}</span>
            </button>

            {showLanguageMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-2 border border-gray-200 dark:border-gray-700 z-50">
                <button
                  onClick={() => {
                    setLanguage('en')
                    setShowLanguageMenu(false)
                  }}
                  className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                    language === 'en' ? 'bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 font-medium' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  English
                </button>
                <button
                  onClick={() => {
                    setLanguage('kn')
                    setShowLanguageMenu(false)
                  }}
                  className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                    language === 'kn' ? 'bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 font-medium' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  ಕನ್ನಡ (Kannada)
                </button>
                <button
                  onClick={() => {
                    setLanguage('hi')
                    setShowLanguageMenu(false)
                  }}
                  className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                    language === 'hi' ? 'bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 font-medium' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  हिन्दी (Hindi)
                </button>
              </div>
            )}
          </div>

          {/* User Profile */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-3 text-gray-700 hover:text-gray-900 transition-colors dark:text-gray-300 dark:hover:text-gray-100"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-teal-400 to-teal-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                {user?.display_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{user?.display_name || user?.username}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user?.role}</p>
              </div>
              <ChevronDown size={18} className="text-gray-400 dark:text-gray-500" />
            </button>

            {/* Profile Dropdown */}
            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-2 border border-gray-200 dark:border-gray-700">
                <Link
                  to="/profile"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-sm"
                  onClick={() => setShowProfileMenu(false)}
                >
                  My Profile
                </Link>
                <button
                  className="w-full text-left px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-sm"
                  onClick={() => setShowProfileMenu(false)}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
