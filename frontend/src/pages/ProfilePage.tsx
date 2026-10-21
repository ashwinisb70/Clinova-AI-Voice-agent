import React from 'react'
import { AppLayout } from '../components/AppLayout'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { AlertCircle, LogOut, User, Shield } from 'lucide-react'

export const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const { addToast } = useToast()

  const handleLogout = () => {
    logout()
    addToast(t('auth.logoutConfirm') || 'Logged out successfully', 'success')
    navigate('/login')
  }

  if (!user) {
    return (
      <AppLayout title={t('profile.title')}>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="text-red-600 dark:text-red-400" size={24} />
          <div>
            <p className="font-medium text-red-900 dark:text-red-300">{t('common.error')}</p>
            <p className="text-red-700 dark:text-red-400 text-sm">User information not available</p>
          </div>
        </div>
      </AppLayout>
    )
  }

  const roleColor = {
    admin: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    staff: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
    patient: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
  }[user.role] || 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300'

  const roleIcon = {
    admin: Shield,
    staff: User,
    patient: User,
  }[user.role] || User

  const RoleIcon = roleIcon

  return (
    <AppLayout title={t('profile.title')}>
      <div className="space-y-6 max-w-3xl">
        {/* Profile Header Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8">
          <div className="flex items-start gap-6 mb-8">
            <div className="w-24 h-24 bg-gradient-to-br from-teal-400 to-teal-600 rounded-full flex items-center justify-center text-white text-3xl font-bold flex-shrink-0">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{user.display_name || user.username}</h1>
              <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">@{user.username}</p>
              <div className="mt-4 flex items-center gap-2">
                <RoleIcon size={18} className="text-gray-400 dark:text-gray-500" />
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${roleColor}`}>
                  {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Personal Information Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <User size={20} className="text-teal-600" />
            {t('profile.personalInfo')}
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Display Name</p>
              <p className="text-gray-900 dark:text-white text-lg">{user.display_name || '-'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Username</p>
              <p className="text-gray-900 dark:text-white text-lg">{user.username}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Role</p>
              <p className="text-gray-900 dark:text-white text-lg capitalize">{user.role}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Hospital ID</p>
              <p className="text-gray-900 dark:text-white text-lg">{user.hospital_id}</p>
            </div>
          </div>
        </div>

        {/* Account Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Account Actions</h2>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600 text-white px-6 py-3 rounded-lg transition-colors font-medium"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </div>
    </AppLayout>
  )
}

export default ProfilePage
