import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { useLanguage } from '../context/LanguageContext'
import { useToast } from '../context/ToastContext'
import { doctorAPI, departmentAPI } from '../services/api'
import { AlertCircle, Users, Award, DollarSign, Plus, X } from 'lucide-react'

interface Doctor {
  doctor_id: string
  name: string
  specialization: string
  department: string
  experience_years: number
  consultation_fee: number
  available: boolean
}

export const Doctors: React.FC = () => {
  const { t } = useLanguage()
  const { addToast } = useToast()
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [departments, setDepartments] = useState<any[]>([])
  const [formData, setFormData] = useState({
    name: '',
    specialization: '',
    department_id: '',
    experience_years: 0,
    consultation_fee: 0
  })
  const [editingId, setEditingId] = useState<string | null>(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [doctorsRes, deptsRes] = await Promise.all([
          doctorAPI.getAll(),
          departmentAPI.getAdminList()
        ])
        setDoctors(doctorsRes.data.doctors || [])
        setDepartments(deptsRes.data.departments || [])
      } catch (err: any) {
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [t])

  const handleAdd = () => {
    setEditingId(null)
    setFormData({ name: '', specialization: '', department_id: '', experience_years: 0, consultation_fee: 0 })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim() || !formData.specialization.trim()) {
      addToast(t('common.fillRequired') || 'Please fill required fields', 'error')
      return
    }

    setIsSubmitting(true)
    try {
      if (editingId) {
        await doctorAPI.update(editingId, formData)
        addToast(t('doctors.updated'), 'success')
      } else {
        await doctorAPI.create(formData)
        addToast(t('doctors.created'), 'success')
      }
      setShowModal(false)
      const res = await doctorAPI.getAll()
      setDoctors(res.data.doctors || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <AppLayout title={t('doctors.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('doctors.title')}>
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
    <AppLayout title={t('doctors.title')}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="text-gray-600 dark:text-gray-400">Medical professionals at our hospital</p>
          </div>
          <button
            onClick={handleAdd}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
          >
            <Plus size={20} />
            {t('doctors.addDoctor')}
          </button>
        </div>

        {/* Add/Edit Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl max-w-md w-full max-h-96 overflow-y-auto">
              <div className="sticky top-0 flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">{editingId ? t('doctors.editDoctor') : t('doctors.addDoctor')}</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400">
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('doctors.doctorName')} *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('doctors.specialization')} *</label>
                  <input
                    type="text"
                    value={formData.specialization}
                    onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('doctors.department')}</label>
                  <select
                    value={formData.department_id}
                    onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="">Select Department</option>
                    {departments.map(d => (
                      <option key={d.department_id} value={d.department_id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Experience (years)</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.experience_years}
                      onChange={(e) => setFormData({ ...formData, experience_years: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Consultation Fee</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.consultation_fee}
                      onChange={(e) => setFormData({ ...formData, consultation_fee: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium disabled:opacity-50"
                  >
                    {isSubmitting ? t('doctors.saving') : t('common.save')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doctor) => (
            <div key={doctor.doctor_id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-navy-900 dark:text-white">{doctor.name}</h3>
                  <p className="text-sm text-teal-600 dark:text-teal-400 font-medium">{doctor.specialization}</p>
                </div>
                {doctor.available && (
                  <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-semibold rounded">{t('doctors.available')}</span>
                )}
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <Award size={16} className="text-gray-400 dark:text-gray-500" />
                  <span>{doctor.experience_years} years experience</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <Users size={16} className="text-gray-400 dark:text-gray-500" />
                  <span>{doctor.department}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <DollarSign size={16} className="text-gray-400 dark:text-gray-500" />
                  <span>₹{doctor.consultation_fee} consultation fee</span>
                </div>

                <div className="pt-3 border-t border-gray-100 dark:border-gray-700 mt-3">
                  <button
                    onClick={() => {
                      setEditingId(doctor.doctor_id)
                      setFormData({
                        name: doctor.name,
                        specialization: doctor.specialization,
                        department_id: doctor.department || '',
                        experience_years: doctor.experience_years,
                        consultation_fee: doctor.consultation_fee
                      })
                      setShowModal(true)
                    }}
                    className="w-full text-sm px-2 py-1 text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-gray-700 rounded transition-colors"
                  >
                    {t('common.edit')}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {doctors.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="text-gray-400 dark:text-gray-500 mx-auto mb-3" size={32} />
            <p className="text-gray-500 dark:text-gray-400">{t('common.noResults')}</p>
          </div>
        )}
      </div>
    </AppLayout>
  )
}

export default Doctors
