import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { useLanguage } from '../context/LanguageContext'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { Users, Calendar, AlertCircle, DollarSign, CheckCircle, Bell } from 'lucide-react'
import { adminAPI } from '../services/api'

interface AdminSummary {
  total_patients: number
  total_appointments: number
  todays_appointments: number
  pending_appointments: number
  completed_appointments: number
  completed_today: number
  revenue: number
  pending_invoices: number
  unread_notifications: number
  active_conversations: number
  open_escalations: number
  email_configured: boolean
}

interface AnalyticsData {
  days: number
  series: any[]
  departments: any[]
  sources: any[]
  statuses: any[]
  payment_methods: any[]
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: number | string
  subtext?: string
  color: 'teal' | 'blue' | 'green' | 'orange'
}

const StatCard: React.FC<StatCardProps> = ({ icon, label, value, subtext, color }) => {
  const colors = {
    teal: 'bg-teal-50 dark:bg-teal-900/20 text-teal-600 dark:text-teal-400',
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    orange: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400',
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg ${colors[color]}`}>{icon}</div>
      </div>
      <p className="text-gray-600 dark:text-gray-400 text-sm font-medium mb-2">{label}</p>
      <p className="text-3xl font-bold text-navy-900 dark:text-white">{value}</p>
      {subtext && <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">{subtext}</p>}
    </div>
  )
}

export const Dashboard: React.FC = () => {
  const { t } = useLanguage()
  const [stats, setStats] = useState<AdminSummary | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [summaryRes, analyticsRes] = await Promise.all([
          adminAPI.getSummary(),
          adminAPI.getAnalytics(7),
        ])
        setStats(summaryRes.data)
        setAnalytics(analyticsRes.data)
      } catch (err: any) {
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadDashboardData()
  }, [t])

  if (isLoading) {
    return (
      <AppLayout title={t('dashboard.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('dashboard.title')}>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="text-red-600 dark:text-red-400" size={24} />
          <div>
            <p className="font-medium text-red-900 dark:text-red-400">{t('common.error')}</p>
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout title={t('dashboard.title')}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <p className="text-gray-600 dark:text-gray-400">{t('dashboard.recentActivity')}</p>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Users size={24} />}
            label={t('dashboard.totalPatients')}
            value={stats?.total_patients || 0}
            color="teal"
          />
          <StatCard
            icon={<Calendar size={24} />}
            label={t('dashboard.todayAppointments')}
            value={stats?.todays_appointments || 0}
            color="blue"
          />
          <StatCard
            icon={<AlertCircle size={24} />}
            label={t('dashboard.pendingAppointments')}
            value={stats?.pending_appointments || 0}
            color="orange"
          />
          <StatCard
            icon={<DollarSign size={24} />}
            label={t('dashboard.revenue')}
            value={`₹${(stats?.revenue || 0).toLocaleString('en-IN')}`}
            color="green"
          />
        </div>

        {/* Secondary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={<CheckCircle size={24} />}
            label={t('dashboard.completedToday')}
            value={stats?.completed_today ?? stats?.completed_appointments ?? 0}
            color="green"
          />
          <StatCard
            icon={<DollarSign size={24} />}
            label={t('dashboard.pendingInvoices')}
            value={stats?.pending_invoices || 0}
            color="orange"
          />
          <StatCard
            icon={<Bell size={24} />}
            label={t('dashboard.unreadNotifications')}
            value={stats?.unread_notifications || 0}
            color="teal"
          />
        </div>

        {/* Charts Section */}
        {analytics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Appointment Trends */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-4">{t('dashboard.appointmentTrends')}</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.series}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#ffffff'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="appointments"
                    stroke="#0d9488"
                    strokeWidth={2}
                    dot={{ fill: '#0d9488', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Revenue Trends */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-4">{t('dashboard.appointmentTrends')}</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.series}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#ffffff'
                    }}
                  />
                  <Bar dataKey="revenue" fill="#0d9488" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Department Breakdown */}
            {analytics.departments && analytics.departments.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-4">{t('dashboard.totalDepartments')}</h3>
                <div className="space-y-3">
                  {analytics.departments.slice(0, 5).map((dept, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className="text-gray-700 dark:text-gray-300">{dept.name}</span>
                      <span className="font-semibold text-navy-900 dark:text-white">{dept.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Appointment Status */}
            {analytics.statuses && analytics.statuses.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-4">{t('appointments.status')}</h3>
                <div className="space-y-3">
                  {analytics.statuses.slice(0, 5).map((status, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className="text-gray-700 dark:text-gray-300">{status.name}</span>
                      <span className="font-semibold text-navy-900 dark:text-white">{status.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}

export default Dashboard
