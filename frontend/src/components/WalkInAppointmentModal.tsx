import React, { useState } from 'react'
import { useLanguage } from '../context/LanguageContext'
import { useToast } from '../context/ToastContext'
import { appointmentAPI } from '../services/api'
import { X, AlertTriangle } from 'lucide-react'

interface WalkInAppointmentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export const WalkInAppointmentModal: React.FC<WalkInAppointmentModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { t } = useLanguage()
  const { addToast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    patient_id: '',
    department: '',
    doctor_id: '',
    is_emergency: false,
    notes: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.patient_id || !formData.department) {
      addToast(t('common.fillRequired'), 'error')
      return
    }

    setIsSubmitting(true)
    try {
      await appointmentAPI.bookWalkIn({
        patient_id: formData.patient_id,
        department: formData.department,
        doctor_id: formData.doctor_id || undefined,
        is_emergency: formData.is_emergency,
        notes: formData.notes || undefined,
      })
      addToast('Walk-in appointment created successfully', 'success')
      setFormData({
        patient_id: '',
        department: '',
        doctor_id: '',
        is_emergency: false,
        notes: '',
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
          <h3 className="text-lg font-bold">Register Walk-in Appointment</h3>
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
              placeholder="e.g., Emergency, General"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Chief complaint or additional notes..."
            />
          </div>

          <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg border border-red-200">
            <input
              type="checkbox"
              id="emergency"
              checked={formData.is_emergency}
              onChange={(e) => setFormData({ ...formData, is_emergency: e.target.checked })}
              className="w-4 h-4 text-red-600 rounded"
            />
            <div className="flex-1">
              <label htmlFor="emergency" className="flex items-center gap-2 font-medium text-red-700 cursor-pointer">
                <AlertTriangle size={16} />
                High Priority / Emergency
              </label>
              <p className="text-xs text-red-600 mt-1">Moves patient to high-priority queue</p>
            </div>
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
              {isSubmitting ? 'Creating...' : 'Register Walk-in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
