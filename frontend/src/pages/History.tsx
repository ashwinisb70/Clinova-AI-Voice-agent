import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { appointmentAPI } from '../services/api'
import { useLanguage } from '../context/LanguageContext'
import { AlertCircle } from 'lucide-react'

interface Appointment {
  appointment_id: string
  patient_name: string
  department: string
  preferred_date: string
  preferred_time: string
  status: string
  created_at: string
}

export const History: React.FC = () => {
  const { t } = useLanguage()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadHistory = async () => {
      try {
        // Load completed appointments
        const res = await appointmentAPI.getAll('completed')
        setAppointments(res.data.appointments || [])
      } catch (err: any) {
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadHistory()
  }, [])

  if (isLoading) {
    return (
      <AppLayout title={t('history.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('history.title')}>
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

  return (
    <AppLayout title={t('history.title')}>
      <div className="space-y-6">
        <div>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">View completed appointments</p>
        </div>

        {/* Stats */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <p className="text-gray-600 dark:text-gray-400 text-sm">Total Completed Appointments</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{appointments.length}</p>
        </div>

        {/* History Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {appointments.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Appointment ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Patient</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Department</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Date & Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Completed On</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {appointments.map((appointment) => (
                  <tr key={appointment.appointment_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 text-sm font-medium text-teal-600 dark:text-teal-400">{appointment.appointment_id}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{appointment.patient_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{appointment.department}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(appointment.preferred_date).toLocaleDateString()} {appointment.preferred_time || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(appointment.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500 dark:text-gray-400">No completed appointments in history</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

export default History
