import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { paymentAPI } from '../services/api'
import { useLanguage } from '../context/LanguageContext'
import { AlertCircle } from 'lucide-react'

interface Payment {
  payment_id: string
  patient_name: string
  invoice_id: string
  amount: number
  status: string
  method: string
  method_label: string
  created_at: string
  paid_at?: string
}

export const Payments: React.FC = () => {
  const { t } = useLanguage()
  const [payments, setPayments] = useState<Payment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadPayments = async () => {
      try {
        const res = await paymentAPI.getAll()
        setPayments(res.data.payments || [])
      } catch (err: any) {
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadPayments()
  }, [])

  if (isLoading) {
    return (
      <AppLayout title={t('payments.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('payments.title')}>
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

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400',
    paid: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400',
    refunded: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400',
  }

  return (
    <AppLayout title={t('payments.title')}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Payments</h2>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">Track all payment transactions</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Payments</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{payments.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Paid</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{payments.filter(p => p.status === 'paid').length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Pending</p>
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">{payments.filter(p => p.status === 'pending').length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Amount</p>
            <p className="text-2xl font-bold text-teal-600 dark:text-teal-400 mt-1">₹{payments.reduce((sum, p) => sum + p.amount, 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
          </div>
        </div>

        {/* Payments Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {payments.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Payment ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Patient</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Method</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {payments.map((payment) => (
                  <tr key={payment.payment_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 text-sm font-medium text-teal-600 dark:text-teal-400">{payment.payment_id}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{payment.patient_name}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">₹{payment.amount.toFixed(2)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{payment.method_label}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[payment.status]}`}>
                        {payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{new Date(payment.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500 dark:text-gray-400">No payments found</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

export default Payments
