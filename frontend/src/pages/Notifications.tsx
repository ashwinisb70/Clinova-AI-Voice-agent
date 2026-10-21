import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { notificationAPI } from '../services/api'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../context/LanguageContext'
import { AlertCircle } from 'lucide-react'

interface Notification {
  notification_id: string
  type: string
  params: Record<string, any>
  read: boolean
  link?: string
  created_at: string
}

export const Notifications: React.FC = () => {
  const { addToast } = useToast()
  const { t } = useLanguage()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showUnreadOnly, setShowUnreadOnly] = useState(false)

  useEffect(() => {
    const loadNotifications = async () => {
      try {
        const res = await notificationAPI.getAll(showUnreadOnly)
        console.log('Notifications API response:', res.data)

        // Handle both direct array response and nested response
        const notifData = Array.isArray(res.data) ? res.data : (res.data.notifications || [])
        console.log('Parsed notifications:', notifData)

        setNotifications(notifData)
      } catch (err: any) {
        console.error('Error loading notifications:', err)
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadNotifications()
  }, [showUnreadOnly])

  const handleMarkAsRead = async (notifId: string) => {
    try {
      await notificationAPI.markAsRead(notifId)
      setNotifications(notifications.map(n => n.notification_id === notifId ? { ...n, read: true } : n))
      addToast(t('notifications.markedRead'), 'success')
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await notificationAPI.markAllAsRead()
      setNotifications(notifications.map(n => ({ ...n, read: true })))
      addToast(t('notifications.allMarkedRead'), 'success')
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    }
  }

  const unreadCount = notifications.filter(n => !n.read).length

  if (isLoading) {
    return (
      <AppLayout title={t('notifications.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('notifications.title')}>
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{t('notifications.title')}</h2>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="text-red-600 dark:text-red-400" size={24} />
            <div>
              <p className="font-medium text-red-900 dark:text-red-400">Error</p>
              <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
            </div>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout title={t('notifications.title')}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">{unreadCount} {t('notifications.unread')}</p>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              className="text-sm text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 font-medium"
            >
              Mark all as read
            </button>
          )}
        </div>

        {/* Filter Toggle */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
              className="w-4 h-4 text-teal-600 dark:bg-gray-700 dark:border-gray-600 rounded"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Show unread only</span>
          </label>
        </div>

        {/* Notifications List */}
        <div className="space-y-3">
          {notifications.length > 0 ? (
            notifications.map((notif) => (
              <div
                key={notif.notification_id}
                className={`rounded-lg border p-4 transition-colors ${
                  notif.read
                    ? 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                    : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {notif.type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </h3>
                      {!notif.read && (
                        <span className="inline-block w-2 h-2 bg-teal-600 rounded-full"></span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {Object.entries(notif.params || {})
                        .map(([key, value]) => `${key}: ${value}`)
                        .join(', ')}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      {new Date(notif.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!notif.read && (
                    <button
                      onClick={() => handleMarkAsRead(notif.notification_id)}
                      className="text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 text-sm font-medium ml-4"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">No notifications found</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

export default Notifications
