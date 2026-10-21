import React, { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useLanguage } from '../context/LanguageContext'
import { authAPI } from '../services/api'
import { Eye, EyeOff, Building2, ArrowRight } from 'lucide-react'

export const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { addToast } = useToast()
  const { t } = useLanguage()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await authAPI.login({ username, password })
      const { access_token } = response.data

      // Save token before calling protected endpoints
      localStorage.setItem('authToken', access_token)

      // Get user info
      const userResponse = await authAPI.me()
      const userData = userResponse.data

      // Store token and user in auth context
      login(access_token, userData)

      addToast(t('auth.login') + ' successful!', 'success')
      navigate('/dashboard')
    } catch (error: any) {
      addToast(error.response?.data?.detail || t('auth.invalidCredentials'), 'error')
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
              Welcome Back to{' '}
              <span className="text-teal-400">Better Hospital Management</span>
            </h2>
            <p className="text-xl text-navy-200 mb-8 leading-relaxed">
              Manage your hospital operations efficiently with CLINOVA's intuitive platform.
            </p>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-teal-500/20 rounded-full flex items-center justify-center">
                  <span className="text-teal-400">✓</span>
                </div>
                <span className="text-navy-100">Streamlined patient management</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-teal-500/20 rounded-full flex items-center justify-center">
                  <span className="text-teal-400">✓</span>
                </div>
                <span className="text-navy-100">Real-time analytics and reporting</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-teal-500/20 rounded-full flex items-center justify-center">
                  <span className="text-teal-400">✓</span>
                </div>
                <span className="text-navy-100">Secure patient data protection</span>
              </div>
            </div>
          </div>

          {/* Right Side - Login Form */}
          <div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 md:p-10">
              <h3 className="text-3xl font-bold text-navy-900 dark:text-white mb-2">{t('auth.login')}</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-8">Enter your credentials to access your account</p>

              <form onSubmit={handleLogin} className="space-y-6">
                {/* Username/Email Field */}
                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    {t('auth.username')} or Email
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="admin or admin@example.com"
                    className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:border-teal-600 dark:focus:border-teal-500 transition-colors"
                    required
                    disabled={isLoading}
                  />
                </div>

                {/* Password Field */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                      {t('auth.password')}
                    </label>
                    <a href="#" className="text-sm text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 font-medium">
                      {t('auth.forgotPassword')}
                    </a>
                  </div>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:border-teal-600 dark:focus:border-teal-500 transition-colors"
                      required
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                    >
                      {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                    </button>
                  </div>
                </div>

                {/* Remember Me & Checkbox */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="remember"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 text-teal-600 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-teal-600"
                    disabled={isLoading}
                  />
                  <label htmlFor="remember" className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                    {t('auth.rememberMe')}
                  </label>
                </div>

                {/* Login Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-teal-600 text-white font-semibold py-3 rounded-lg hover:bg-teal-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                      Loading...
                    </>
                  ) : (
                    <>
                      {t('auth.login')}
                      <ArrowRight size={20} />
                    </>
                  )}
                </button>
              </form>

              {/* Divider */}
              <div className="my-6 flex items-center gap-4">
                <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
                <span className="text-sm text-gray-500 dark:text-gray-400">or</span>
                <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
              </div>

              {/* Sign Up Link */}
              <p className="text-center text-gray-600 dark:text-gray-400">
                {t('auth.noAccount')}{' '}
                <Link to="/signup" className="text-teal-600 dark:text-teal-400 font-semibold hover:text-teal-700 dark:hover:text-teal-300">
                  {t('auth.signupHere')}
                </Link>
              </p>

            </div>

            {/* Footer Text */}
            <p className="text-center text-navy-200 text-sm mt-6">
              &copy; 2026 CLINOVA. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
