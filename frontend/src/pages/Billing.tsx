import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { invoiceAPI } from '../services/api'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../context/LanguageContext'
import { AlertCircle, CreditCard } from 'lucide-react'
import { PaymentModal } from '../components/PaymentModal'

interface Invoice {
  invoice_id: string
  patient_name: string
  appointment_id: string
  total: number
  status: string
  created_at: string
  paid_at?: string
}

type StatusFilter = '' | 'pending' | 'paid' | 'failed' | 'cancelled' | 'refunded'

export const Billing: React.FC = () => {
  const { addToast } = useToast()
  const { t } = useLanguage()
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('')
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)
  const [showPaymentModal, setShowPaymentModal] = useState(false)

  useEffect(() => {
    loadInvoices()
  }, [statusFilter])

  const handlePayNow = (invoice: Invoice) => {
    setSelectedInvoice(invoice)
    setShowPaymentModal(true)
  }

  const handlePaymentSuccess = () => {
    setShowPaymentModal(false)
    setSelectedInvoice(null)
    addToast(t('billing.paymentSuccess'), 'success')
    loadInvoices()
  }

  const loadInvoices = async () => {
    try {
      const res = await invoiceAPI.getAll(statusFilter || undefined)
      setInvoices(res.data.invoices || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <AppLayout title={t('billing.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('billing.title')}>
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

  const statuses: StatusFilter[] = ['', 'pending', 'paid', 'failed', 'cancelled', 'refunded']
  const statusLabels: Record<StatusFilter, string> = {
    '': 'All',
    pending: 'Pending',
    paid: 'Paid',
    failed: 'Failed',
    cancelled: 'Cancelled',
    refunded: 'Refunded',
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    paid: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
    refunded: 'bg-blue-100 text-blue-800',
  }

  return (
    <AppLayout title={t('billing.title')}>
      <div className="space-y-6">
        <div>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">{t('billing.manage')}</p>
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

        {/* Payment Modal */}
        {showPaymentModal && selectedInvoice && (
          <PaymentModal
            invoiceId={selectedInvoice.invoice_id}
            invoiceAmount={selectedInvoice.total}
            patientName={selectedInvoice.patient_name}
            onSuccess={handlePaymentSuccess}
            onClose={() => setShowPaymentModal(false)}
          />
        )}

        {/* Invoices Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {invoices.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Invoice ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Patient</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {invoices.map((invoice) => (
                  <tr key={invoice.invoice_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 text-sm font-medium text-teal-600 dark:text-teal-400">{invoice.invoice_id}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{invoice.patient_name}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">₹{invoice.total.toFixed(2)}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[invoice.status]}`}>
                        {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{new Date(invoice.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-sm">
                      {invoice.status === 'pending' && (
                        <button
                          onClick={() => handlePayNow(invoice)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-600 text-white text-xs font-medium rounded hover:bg-teal-700 transition-colors"
                        >
                          <CreditCard size={14} />
                          Pay Now
                        </button>
                      )}
                      {invoice.status !== 'pending' && (
                        <span className="text-xs text-gray-500">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500 dark:text-gray-400">No invoices found</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

export default Billing
