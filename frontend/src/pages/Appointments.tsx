import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { appointmentAPI, adminAPI, departmentAPI, doctorAPI } from '../services/api'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../context/LanguageContext'
import { RecurringAppointmentModal } from '../components/RecurringAppointmentModal'
import { WalkInAppointmentModal } from '../components/WalkInAppointmentModal'
import { AlertCircle, Plus, X } from 'lucide-react'

interface Appointment {
  appointment_id: string
  patient_name: string
  patient_id?: string
  department: string
  doctor_id?: string
  preferred_date: string
  preferred_time: string
  status: string
  created_at: string
  source?: string
}

type StatusFilter = '' | 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'rescheduled'

export const Appointments: React.FC = () => {
  const { addToast } = useToast()
  const { t } = useLanguage()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('')
  const [cancelReason, setCancelReason] = useState('')
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [showRescheduleModal, setShowRescheduleModal] = useState(false)
  const [rescheduleDate, setRescheduleDate] = useState('')
  const [rescheduleTime, setRescheduleTime] = useState('10:00')
  const [rescheduleSubmitting, setRescheduleSubmitting] = useState(false)
  const [showRecurringModal, setShowRecurringModal] = useState(false)
  const [showWalkInModal, setShowWalkInModal] = useState(false)
  const [showBookModal, setShowBookModal] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
  const [patients, setPatients] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [doctors, setDoctors] = useState<any[]>([])
  const [bookIsSubmitting, setBookIsSubmitting] = useState(false)
  const [bookFormData, setBookFormData] = useState({
    patient_id: '',
    department: '',
    doctor_id: '',
    preferred_date: '',
    preferred_time: '10:00',
    notes: ''
  })

  useEffect(() => {
    const loadData = async () => {
      try {
        const [apptRes, patRes, deptRes, docRes] = await Promise.all([
          appointmentAPI.getAll(statusFilter || undefined),
          adminAPI.getPatients().catch(() => ({ data: { patients: [] } })),
          departmentAPI.getAll(),
          doctorAPI.getAll()
        ])
        setAppointments(apptRes.data.appointments || [])
        setPatients(patRes.data.patients || [])
        setDepartments(deptRes.data.departments || deptRes.data || [])
        setDoctors(docRes.data.doctors || docRes.data || [])
      } catch (err: any) {
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [statusFilter, t])

  const handleBookAppointment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!bookFormData.patient_id || !bookFormData.department || !bookFormData.preferred_date) {
      addToast(t('common.fillRequired') || 'Please fill required fields', 'error')
      return
    }

    setBookIsSubmitting(true)
    try {
      await appointmentAPI.staffBook({
        patient_id: bookFormData.patient_id,
        department: bookFormData.department,
        doctor_id: bookFormData.doctor_id || undefined,
        preferred_date: bookFormData.preferred_date,
        preferred_time: bookFormData.preferred_time,
        notes: bookFormData.notes || undefined
      })
      addToast(t('appointments.booked'), 'success')
      setShowBookModal(false)
      setBookFormData({
        patient_id: '',
        department: '',
        doctor_id: '',
        preferred_date: '',
        preferred_time: '10:00',
        notes: ''
      })
      const res = await appointmentAPI.getAll(statusFilter || undefined)
      setAppointments(res.data.appointments || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    } finally {
      setBookIsSubmitting(false)
    }
  }

  const filteredDoctors = bookFormData.department
    ? doctors.filter(d => d.department === bookFormData.department || d.department_id === bookFormData.department)
    : doctors

  const handleCancelClick = (appointment: Appointment) => {
    setSelectedAppointment(appointment)
    setCancelReason('')
    setShowCancelModal(true)
  }

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedAppointment) return

    try {
      await appointmentAPI.cancel(selectedAppointment.appointment_id, cancelReason)
      addToast(t('appointments.cancelledSuccess'), 'success')
      setShowCancelModal(false)
      // Reload appointments
      const res = await appointmentAPI.getAll(statusFilter || undefined)
      setAppointments(res.data.appointments || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    }
  }

  const handleRescheduleClick = (appointment: Appointment) => {
    setSelectedAppointment(appointment)
    setRescheduleDate(appointment.preferred_date?.slice(0, 10) || '')
    setRescheduleTime(appointment.preferred_time?.slice(0, 5) || '10:00')
    setShowRescheduleModal(true)
  }

  const handleRescheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedAppointment || !rescheduleDate || !rescheduleTime) {
      addToast('Please select a date and time', 'error')
      return
    }

    setRescheduleSubmitting(true)
    try {
      await appointmentAPI.reschedule(selectedAppointment.appointment_id, {
        preferred_date: rescheduleDate,
        preferred_time: rescheduleTime,
      })

      addToast('Appointment rescheduled successfully', 'success')
      setShowRescheduleModal(false)
      const res = await appointmentAPI.getAll(statusFilter || undefined)
      setAppointments(res.data.appointments || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || 'Unable to reschedule appointment', 'error')
    } finally {
      setRescheduleSubmitting(false)
    }
  }

  const handleStatusChange = async (appointment: Appointment, status: 'confirmed' | 'completed') => {
    try {
      await appointmentAPI.updateStatus(appointment.appointment_id, status)
      addToast(t('appointments.statusUpdated'), 'success')
      const res = await appointmentAPI.getAll(statusFilter || undefined)
      setAppointments(res.data.appointments || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    }
  }

  if (isLoading) {
    return (
      <AppLayout title={t('appointments.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('appointments.title')}>
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

  const statuses: StatusFilter[] = ['', 'pending', 'confirmed', 'completed', 'cancelled', 'rescheduled']
  const statusLabels: Record<StatusFilter, string> = {
    '': 'All',
    'pending': 'Pending',
    'confirmed': 'Confirmed',
    'completed': 'Completed',
    'cancelled': 'Cancelled',
    'rescheduled': 'Rescheduled',
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    confirmed: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
    rescheduled: 'bg-purple-100 text-purple-800',
  }

  return (
    <AppLayout title={t('appointments.title')}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">{t('appointments.bookAppointment')}</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setShowBookModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
            >
              <Plus size={20} />
              {t('appointments.bookAppointment')}
            </button>
            <button
              onClick={() => setShowRecurringModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={20} />
              Recurring
            </button>
            <button
              onClick={() => setShowWalkInModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <Plus size={20} />
              Walk-in
            </button>
          </div>
        </div>

        {/* Status Filter */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex-shrink-0">{t('appointments.status')}:</span>
            {statuses.map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1 rounded-full text-sm font-medium flex-shrink-0 transition-colors ${
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

        {/* Book Appointment Modal */}
        {showBookModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl max-w-md w-full max-h-96 overflow-y-auto">
              <div className="sticky top-0 flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">{t('appointments.bookAppointment')}</h3>
                <button onClick={() => setShowBookModal(false)} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400">
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleBookAppointment} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('appointments.patientName')} *</label>
                  <select
                    value={bookFormData.patient_id}
                    onChange={(e) => setBookFormData({ ...bookFormData, patient_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    required
                  >
                    <option value="">{t('appointments.selectPatient')}</option>
                    {patients.map(p => (
                      <option key={p.patient_id} value={p.patient_id}>
                        {p.full_name || p.name || p.patient_name || `Patient ${p.patient_id}`}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('appointments.department')} *</label>
                  <select
                    value={bookFormData.department}
                    onChange={(e) => setBookFormData({ ...bookFormData, department: e.target.value, doctor_id: '' })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    required
                  >
                    <option value="">{t('appointments.selectDept')}</option>
                    {departments.map(d => (
                      <option key={d.department_id} value={d.name || d.department_id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('appointments.doctor')}</label>
                  <select
                    value={bookFormData.doctor_id}
                    onChange={(e) => setBookFormData({ ...bookFormData, doctor_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="">Auto-assign</option>
                    {filteredDoctors.map(d => (
                      <option key={d.doctor_id} value={d.doctor_id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('appointments.date')} *</label>
                  <input
                    type="date"
                    value={bookFormData.preferred_date}
                    onChange={(e) => setBookFormData({ ...bookFormData, preferred_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('appointments.time')}</label>
                  <input
                    type="time"
                    value={bookFormData.preferred_time}
                    onChange={(e) => setBookFormData({ ...bookFormData, preferred_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('appointments.notes')}</label>
                  <textarea
                    value={bookFormData.notes}
                    onChange={(e) => setBookFormData({ ...bookFormData, notes: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div className="flex gap-2 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowBookModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="submit"
                    disabled={bookIsSubmitting}
                    className="flex-1 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium disabled:opacity-50"
                  >
                    {bookIsSubmitting ? t('common.loading') : t('appointments.bookAppointment')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Recurring Modal */}
        <RecurringAppointmentModal
          isOpen={showRecurringModal}
          onClose={() => setShowRecurringModal(false)}
          onSuccess={() => {
            const res = appointmentAPI.getAll(statusFilter || undefined)
            res.then(r => setAppointments(r.data.appointments || []))
          }}
        />

        {/* Walk-in Modal */}
        <WalkInAppointmentModal
          isOpen={showWalkInModal}
          onClose={() => setShowWalkInModal(false)}
          onSuccess={() => {
            const res = appointmentAPI.getAll(statusFilter || undefined)
            res.then(r => setAppointments(r.data.appointments || []))
          }}
        />

        {/* Cancel Modal */}
        {showCancelModal && selectedAppointment && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-bold">Cancel Appointment</h3>
              </div>

              <form onSubmit={handleCancelSubmit} className="p-6 space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-2">
                    Are you sure you want to cancel this appointment for <strong>{selectedAppointment.patient_name}</strong>?
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reason (optional)</label>
                  <textarea
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    placeholder="Enter cancellation reason..."
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowCancelModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
                  >
                    Keep Appointment
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Reschedule Appointment Modal */}
        {showRescheduleModal && selectedAppointment && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full shadow-xl">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-bold text-gray-900">Reschedule Appointment</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Patient: {selectedAppointment.patient_name}
                </p>
              </div>

              <form onSubmit={handleRescheduleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">New Date</label>
                  <input
                    type="date"
                    required
                    min={new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10)}
                    value={rescheduleDate}
                    onChange={(e) => setRescheduleDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">New Time</label>
                  <input
                    type="time"
                    required
                    value={rescheduleTime}
                    onChange={(e) => setRescheduleTime(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    disabled={rescheduleSubmitting}
                    onClick={() => setShowRescheduleModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium disabled:opacity-50"
                  >
                    Close
                  </button>
                  <button
                    type="submit"
                    disabled={rescheduleSubmitting}
                    className="flex-1 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium disabled:opacity-50"
                  >
                    {rescheduleSubmitting ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Appointments Table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {appointments.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Appointment ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Patient</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Department</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Date & Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {appointments.map((appointment) => (
                  <tr key={appointment.appointment_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-teal-600">{appointment.appointment_id}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{appointment.patient_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{appointment.department}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(appointment.preferred_date).toLocaleDateString()} {appointment.preferred_time || 'â€”'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[appointment.status] || 'bg-gray-100 text-gray-800'}`}>
                        {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm space-x-4">
                      {appointment.status === 'pending' && (
                        <button
                          onClick={() => handleStatusChange(appointment, 'confirmed')}
                          className="text-teal-600 hover:text-teal-700 font-medium text-sm"
                        >
                          {t('appointments.confirm')}
                        </button>
                      )}
                      {appointment.status === 'confirmed' && (
                        <button
                          onClick={() => handleStatusChange(appointment, 'completed')}
                          className="text-teal-600 hover:text-teal-700 font-medium text-sm"
                        >
                          {t('appointments.complete')}
                        </button>
                      )}
                      {appointment.status !== 'cancelled' && appointment.status !== 'completed' && (
                        <button
                          onClick={() => handleRescheduleClick(appointment)}
                          className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                        >
                          Reschedule
                        </button>
                      )}
                      {appointment.status !== 'cancelled' && appointment.status !== 'completed' && (
                        <button
                          onClick={() => handleCancelClick(appointment)}
                          className="text-red-600 hover:text-red-700 font-medium text-sm"
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">No appointments found</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

export default Appointments

