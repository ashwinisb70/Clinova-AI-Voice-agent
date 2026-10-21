import React, { useState } from 'react'
import { useLanguage } from '../context/LanguageContext'
import { useToast } from '../context/ToastContext'
import { appointmentAPI } from '../services/api'
import { X } from 'lucide-react'

interface RecurringAppointmentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export const RecurringAppointmentModal: React.FC<RecurringAppointmentModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { t } = useLanguage()
  const { addToast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    patient_id: '',
    department: '',
    doctor_id: '',
    first_date: '',
    appointment_time: '09:00',
    frequency: 'weekly',
    occurrences: 4,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.patient_id || !formData.department || !formData.first_date) {
      addToast(t('common.fillRequired'), 'error')
      return
    }

    setIsSubmitting(true)
    try {
      await appointmentAPI.bookRecurring({
        patient_id: formData.patient_id,
        department: formData.department,
        doctor_id: formData.doctor_id || undefined,
        first_date: formData.first_date,
        appointment_time: formData.appointment_time,
        frequency: formData.frequency,
        occurrences: parseInt(formData.occurrences.toString()),
      })
      addToast('Recurring appointments created successfully', 'success')
      setFormData({
        patient_id: '',
        department: '',
        doctor_id: '',
        first_date: '',
        appointment_time: '09:00',
        frequency: 'weekly',
        occurrences: 4,
      })
      onSuccess()
      onClose()
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-bold">Book Recurring Appointment</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Patient ID *</label>
            <input
              type="text"
              value={formData.patient_id}
              onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Enter patient ID"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Department *</label>
            <input
              type="text"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="e.g., Cardiology"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Doctor ID (Optional)</label>
            <input
              type="text"
              value={formData.doctor_id}
              onChange={(e) => setFormData({ ...formData, doctor_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Leave blank to auto-assign"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">First Appointment Date *</label>
            <input
              type="date"
              value={formData.first_date}
              onChange={(e) => setFormData({ ...formData, first_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Time *</label>
            <input
              type="time"
              value={formData.appointment_time}
              onChange={(e) => setFormData({ ...formData, appointment_time: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Frequency *</label>
            <select
              value={formData.frequency}
              onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="biweekly">Bi-weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Number of Occurrences (1-52) *</label>
            <input
              type="number"
              min="1"
              max="52"
              value={formData.occurrences}
              onChange={(e) => setFormData({ ...formData, occurrences: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              required
            />
          </div>

          <div className="flex gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium disabled:opacity-50"
            >
              {isSubmitting ? 'Creating...' : 'Book Series'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
