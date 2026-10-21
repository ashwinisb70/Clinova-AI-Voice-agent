import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { useLanguage } from '../context/LanguageContext'
import { useToast } from '../context/ToastContext'
import { departmentAPI } from '../services/api'
import { AlertCircle, Users, Plus, X } from 'lucide-react'

interface Department {
  department_id: string
  name: string
  description?: string
  doctor_count?: number
}

export const Departments: React.FC = () => {
  const { t } = useLanguage()
  const { addToast } = useToast()
  const [departments, setDepartments] = useState<Department[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({ name: '', description: '' })
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    const loadDepartments = async () => {
      try {
        const res = await departmentAPI.getAdminList()
        setDepartments(res.data.departments || [])
      } catch (err: any) {
        setError(err.response?.data?.detail || t('common.error'))
      } finally {
        setIsLoading(false)
      }
    }

    loadDepartments()
  }, [t])

  const handleAdd = () => {
    setEditingId(null)
    setFormData({ name: '', description: '' })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      addToast(t('common.fillRequired') || 'Please fill required fields', 'error')
      return
    }

    setIsSubmitting(true)
    try {
      if (editingId) {
        await departmentAPI.update(editingId, formData)
        addToast('Department updated successfully', 'success')
      } else {
        await departmentAPI.create(formData)
        addToast('Department created successfully', 'success')
      }
      setShowModal(false)
      // Reload departments
      const res = await departmentAPI.getAdminList()
      setDepartments(res.data.departments || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingId) return

    setIsSubmitting(true)
    try {
      await departmentAPI.delete(deletingId)
      addToast('Department deleted successfully', 'success')
      setShowDeleteConfirm(false)
      setDeletingId(null)
      // Reload departments
      const res = await departmentAPI.getAdminList()
      setDepartments(res.data.departments || [])
    } catch (err: any) {
      addToast(err.response?.data?.detail || t('common.error'), 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <AppLayout title={t('departments.title')}>
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title={t('departments.title')}>
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
    <AppLayout title={t('departments.title')}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="text-gray-600 dark:text-gray-400">{t('departments.addDepartment')}</p>
          </div>
          <button
            onClick={handleAdd}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
          >
            <Plus size={20} />
            {t('departments.addDepartment')}
          </button>
        </div>

        {/* Add/Edit Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl max-w-md w-full">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">{editingId ? t('departments.editDept') : t('departments.addDepartment')}</h3>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('departments.deptName')} *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('departments.desc')}</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
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
                    {isSubmitting ? t('departments.saving') : t('common.save')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && deletingId && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg max-w-sm w-full">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">{t('departments.deleteConfirm')}</h3>
              </div>

              <div className="p-6">
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {t('departments.deleteMsg')}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('departments.deleteWarning')}
                </p>
              </div>

              <div className="flex gap-2 p-6 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setDeletingId(null)
                  }}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium disabled:opacity-50"
                >
                  {isSubmitting ? t('departments.deleting') : t('common.delete')}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {departments.map((dept) => (
            <div key={dept.department_id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-navy-900 dark:text-white">{dept.name}</h3>
                </div>
              </div>

              {dept.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{dept.description}</p>
              )}

              {dept.doctor_count !== undefined && (
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-4">
                  <Users size={16} className="text-gray-400 dark:text-gray-500" />
                  <span>{dept.doctor_count} {t('departments.doctors')}</span>
                </div>
              )}

              <div className="flex gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                <button
                  onClick={() => {
                    setEditingId(dept.department_id)
                    setFormData({ name: dept.name, description: dept.description || '' })
                    setShowModal(true)
                  }}
                  className="flex-1 text-sm px-2 py-1 text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  {t('common.edit')}
                </button>
                <button
                  onClick={() => {
                    setDeletingId(dept.department_id)
                    setShowDeleteConfirm(true)
                  }}
                  className="flex-1 text-sm px-2 py-1 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  {t('common.delete')}
                </button>
              </div>
            </div>
          ))}
        </div>

        {departments.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="text-gray-400 dark:text-gray-500 mx-auto mb-3" size={32} />
            <p className="text-gray-500 dark:text-gray-400">{t('common.noResults')}</p>
          </div>
        )}
      </div>
    </AppLayout>
  )
}

export default Departments
