import React, { useEffect, useState } from 'react'
import { hospitalAPI } from '../services/api'

const HospitalSettings: React.FC = () => {
  const [phone, setPhone] = useState('')
  const [currentPhone, setCurrentPhone] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    const loadSettings = async () => {
      try {
        const response = await hospitalAPI.getDetails()
        const hospital = response.data?.hospital
        const savedPhone = hospital?.ai_receptionist_phone || ''

        if (active) {
          const configured =
            savedPhone === 'your_ai_receptionist_phone_here' ? '' : savedPhone

          setPhone(configured)
          setCurrentPhone(configured)
        }
      } catch {
        if (active) {
          setError('Could not load hospital settings. Please try again.')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    loadSettings()
    return () => {
      active = false
    }
  }, [])

  const handleSave = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMessage('')
    setError('')

    const normalizedPhone = phone.trim().replace(/[\s\-()]/g, '')

    if (!/^\+?[0-9]{10,13}$/.test(normalizedPhone)) {
      setError('Enter a valid phone number containing 10–13 digits, optionally starting with +.')
      return
    }

    try {
      setSaving(true)

      await hospitalAPI.updateDetails({
        ai_receptionist_phone: normalizedPhone,
      })

      setPhone(normalizedPhone)
      setCurrentPhone(normalizedPhone)
      setMessage('Hospital settings saved successfully.')
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          'Unable to save settings. Check your admin login and backend.'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6 md:p-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <p className="text-sm font-medium text-teal-600 mb-2">
            CLINOVA / ADMINISTRATION
          </p>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Hospital Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Configure the phone number displayed for your AI receptionist.
          </p>
        </div>

        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 rounded-xl bg-teal-50 dark:bg-teal-900/30 flex items-center justify-center text-teal-600 text-xl">
              ☎
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                AI Receptionist
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Hospital contact configuration
              </p>
            </div>
          </div>

          {loading ? (
            <p className="text-gray-500">Loading hospital settings...</p>
          ) : (
            <form onSubmit={handleSave} className="space-y-5">
              <div>
                <label
                  htmlFor="receptionist-phone"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  AI Receptionist Phone Number
                </label>
                <input
                  id="receptionist-phone"
                  type="tel"
                  autoComplete="tel"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="+919876543210"
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-4 py-3 outline-none focus:ring-2 focus:ring-teal-500"
                  required
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  Enter the real, authorized receptionist number. Use 10–13 digits, optionally prefixed with +.
                </p>
              </div>

              <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-4">
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  Saving this number does not test Bolna or place a call. The
                  actual phone and Bolna agent configuration must also be valid.
                </p>
              </div>

              {currentPhone && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Currently saved number: {currentPhone}
                </p>
              )}

              {error && (
                <p role="alert" className="text-sm text-red-600">
                  {error}
                </p>
              )}

              {message && (
                <p role="status" className="text-sm text-teal-700 dark:text-teal-400">
                  {message}
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
                className="w-full sm:w-auto px-6 py-3 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-60 text-white font-medium transition-colors"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </form>
          )}
        </section>
      </div>
    </div>
  )
}

export default HospitalSettings
