
import React, { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../context/LanguageContext'
import { authAPI } from '../services/api'
import { Eye, EyeOff, Building2, ArrowRight } from 'lucide-react'

export const SignupPage: React.FC = () => {
  const navigate = useNavigate()
  const { addToast } = useToast()
  const { t } = useLanguage()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const handleSignup = async (e: FormEvent) => {
    e.preventDefault()

    if (password !== confirmPassword) {
      addToast('Passwords do not match', 'error')
      return
    }

    if (password.length < 8) {
      addToast('Password must be at least 8 characters', 'error')
      return
    }

    setIsLoading(true)

    try {
      await authAPI.register({ username, password })

      addToast(
        'Account created successfully. Please log in.',
        'success'
      )
      navigate('/login')
    } catch (error: any) {
      const status = error.response?.status
      const detail = error.response?.data?.detail

      if (status === 403) {
        addToast(
          'Only an authorized hospital admin can create additional staff accounts.',
          'error'
        )
      } else {
        addToast(
          detail || 'Signup failed. Please try again.',
          'error'
        )
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 via-navy-800 to-teal-900 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-5xl">
        <div className="grid md:grid-cols-2 gap-8 items-center">
          {/* Left Side - Branding */}
          <div className="hidden md:block text-white">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 bg-teal-500 rounded-lg flex items-center justify-center">
                <Building2 size={28} />
              </div>
              <h1 className="text-4xl font-bold">CLINOVA</h1>
            </div>

            <h2 className="text-5xl font-bold mb-6 leading-tight">
              Join the Future of{' '}
              <span className="text-teal-400">
                Hospital Management
              </span>
            </h2>

            <p className="text-xl text-navy-200 mb-8 leading-relaxed">
              Create your account to access Clinova hospital management.
            </p>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-teal-500/20 rounded-full flex items-center justify-center">
                  <span className="text-teal-400">✓</span>
                </div>
                <span className="text-navy-100">
                  Easy onboarding process
                </span>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-teal-500/20 rounded-full flex items-center justify-center">
                  <span className="text-teal-400">✓</span>
                </div>
                <span className="text-navy-100">
                  24/7 customer support
                </span>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-teal-500/20 rounded-full flex items-center justify-center">
                  <span className="text-teal-400">✓</span>
                </div>
                <span className="text-navy-100">
                  Secure hospital management
                </span>
              </div>
            </div>
          </div>

          {/* Right Side - Signup Form */}
          <div>
            <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-10">
              <h3 className="text-3xl font-bold text-navy-900 mb-2">
                {t('auth.signup')}
              </h3>

              <p className="text-gray-600 mb-8">
                Create your staff account
              </p>

              <form onSubmit={handleSignup} className="space-y-6">
                {/* Username Field */}
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    {t('auth.username')}
                  </label>

                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Choose a username"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-teal-600 transition-colors text-gray-900"
                    required
                    disabled={isLoading}
                    minLength={3}
                    autoComplete="username"
                  />
                </div>

                {/* Password Field */}
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    {t('auth.password')}
                  </label>

                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min 8 characters"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-teal-600 transition-colors text-gray-900"
                      required
                      disabled={isLoading}
                      minLength={8}
                      autoComplete="new-password"
                    />

                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <EyeOff size={20} />
                      ) : (
                        <Eye size={20} />
                      )}
                    </button>
                  </div>
                </div>

                {/* Confirm Password Field */}
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    {t('auth.passwordConfirm')}
                  </label>

                  <div className="relative">
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm your password"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-teal-600 transition-colors text-gray-900"
                      required
                      disabled={isLoading}
                      minLength={8}
                      autoComplete="new-password"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      aria-label={
                        showConfirmPassword
                          ? 'Hide confirmation password'
                          : 'Show confirmation password'
                      }
                    >
                      {showConfirmPassword ? (
                        <EyeOff size={20} />
                      ) : (
                        <Eye size={20} />
                      )}
                    </button>
                  </div>
                </div>

                {/* Signup Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-teal-600 text-white font-semibold py-3 rounded-lg hover:bg-teal-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                      Creating account...
                    </>
                  ) : (
                    <>
                      {t('auth.signup')}
                      <ArrowRight size={20} />
                    </>
                  )}
                </button>
              </form>

              {/* Login Link */}
              <div className="my-6 flex items-center gap-4">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-sm text-gray-500">or</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              <p className="text-center text-gray-600">
                {t('auth.haveAccount')}{' '}
                <Link
                  to="/login"
                  className="text-teal-600 font-semibold hover:text-teal-700"
                >
                  {t('auth.loginHere')}
                </Link>
              </p>
            </div>

            {/* Footer */}
            <p className="text-center text-navy-200 text-sm mt-6">
              &copy; 2026 CLINOVA. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SignupPage
