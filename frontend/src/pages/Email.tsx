import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { adminAPI } from '../services/api'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../context/LanguageContext'
import { AlertCircle, RotateCcw } from 'lucide-react'

interface EmailLog {
  email_id: string
  recipient: string
  subject: string
  email_type: string
  status: string
  created_at: string
  error?: string
}

type StatusFilter = '' | 'sent' | 'pending' | 'failed'

export const Email: React.FC = () => {
  const { addToast } = useToast()
  const { t } = useLanguage()
  const [emails, setEmails] = useState<EmailLog[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('')

  useEffect(() => {
    const loadEmails = async () => {
      try {
        const res = await adminAPI.getEmailLogs(statusFilter || undefined)
        setEmails(res.data.emails || [])
      } catch (err: any) {
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadEmails()
  }, [statusFilter])

  const handleRetry = async (emailId: string) => {
    try {
      await adminAPI.retryEmail(emailId)
      addToast(t('email.retryInitiated'), 'success')
      // Reload emails
      const res = await adminAPI.getEmailLogs(statusFilter || undefined)
      setEmails(res.data.emails || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    }
  }

  if (isLoading) {
    return (
      <AppLayout title="Email Logs">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title="Email Logs">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="text-red-600 dark:text-red-400" size={24} />
          <div>
            <p className="font-medium text-red-900 dark:text-red-400">Error</p>
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        </div>
      </AppLayout>
    )
  }

  const statuses: StatusFilter[] = ['', 'sent', 'pending', 'failed']
  const statusLabels: Record<StatusFilter, string> = {
    '': 'All',
    sent: 'Sent',
    pending: 'Pending',
    failed: 'Failed',
  }

  const statusColors: Record<string, string> = {
    sent: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400',
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400',
  }

  return (
    <AppLayout title={t('email.title')}>
      <div className="space-y-6">
        <div>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">View email delivery history</p>
        </div>

        {/* Status Filter */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex-shrink-0">Filter:</span>
            {statuses.map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 rounded-full text-sm font-medium flex-shrink-0 ${
                  statusFilter === status
                    ? 'bg-teal-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {statusLabels[status]}
              </button>
            ))}
          </div>
        </div>

        {/* Email Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {emails.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Recipient</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Subject</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {emails.map((email) => (
                  <tr key={email.email_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{email.recipient}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{email.subject}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{email.email_type}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[email.status]}`}>
                        {email.status.charAt(0).toUpperCase() + email.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{new Date(email.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4 text-sm">
                      {email.status === 'failed' && (
                        <button
                          onClick={() => handleRetry(email.email_id)}
                          className="text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 font-medium flex items-center gap-1"
                        >
                          <RotateCcw size={16} />
                          Retry
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">No email logs found</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

export default Email
