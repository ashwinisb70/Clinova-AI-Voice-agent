import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Users, Stethoscope, Calendar, Shield, ArrowRight, Play, Phone, Lock, Users2, Zap } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { WatchDemoModal } from '../components/WatchDemoModal'
import { HospitalImageCarousel } from '../components/HospitalImageCarousel'

export const LandingPage: React.FC = () => {
  const { t } = useLanguage()
  const [showDemoModal, setShowDemoModal] = useState(false)

  const heroFeatures = [
    { icon: Users, label: t('landing.patientManagement') },
    { icon: Stethoscope, label: t('landing.doctorLabel') },
    { icon: Calendar, label: t('landing.appointmentLabel') },
    { icon: Shield, label: t('landing.secureCompliant') },
  ]

  const benefitItems = [
    { icon: Phone, title: t('landing.emergency24'), desc: t('landing.emergencyDesc') },
    { icon: Lock, title: t('landing.secure'), desc: t('landing.hipaaDesc') },
    { icon: Users2, title: t('landing.multiDept'), desc: t('landing.multiDeptDesc') },
    { icon: Zap, title: t('landing.realTime'), desc: t('landing.instantDesc') },
  ]

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Hero Section */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left Column - Text Content */}
            <div>
              {/* Badge */}
              <div className="inline-flex items-center gap-2 bg-teal-50 dark:bg-teal-900/20 px-4 py-2 rounded-full mb-6">
                <Stethoscope size={16} className="text-teal-600 dark:text-teal-400" />
                <span className="text-sm font-medium text-teal-600 dark:text-teal-400">
                  {t('landing.smartHealthcare')}
                </span>
              </div>

              {/* Main Headline */}
              <h1 className="text-5xl md:text-6xl font-bold text-navy-900 dark:text-white leading-tight mb-6">
                {t('landing.betterHealthcare')}{' '}
                <span className="text-teal-600 dark:text-teal-400">{t('landing.clinova')}</span>
              </h1>

              {/* Description */}
              <p className="text-lg text-gray-600 dark:text-gray-300 mb-8 leading-relaxed max-w-xl">
                {t('landing.heroDescription')}
              </p>

              {/* Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <Link
                  to="/signup"
                  className="inline-flex items-center justify-center gap-2 px-8 py-3 bg-teal-600 dark:bg-teal-500 text-white font-semibold rounded-lg hover:bg-teal-700 dark:hover:bg-teal-600 transition-colors"
                >
                  {t('landing.getStartedFree')}
                  <ArrowRight size={20} />
                </Link>
                <button
                  onClick={() => setShowDemoModal(true)}
                  className="inline-flex items-center justify-center gap-2 px-8 py-3 border-2 border-gray-300 dark:border-gray-600 text-navy-900 dark:text-white font-semibold rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <Play size={20} />
                  {t('landing.watchDemo')}
                </button>
              </div>

              {/* Feature Items */}
              <div className="grid grid-cols-2 gap-4">
                {heroFeatures.map((feature, idx) => {
                  const Icon = feature.icon
                  return (
                    <div key={idx} className="flex items-center gap-3 text-gray-700 dark:text-gray-300">
                      <Icon size={20} className="text-teal-600 dark:text-teal-400 flex-shrink-0" />
                      <span className="font-medium text-sm">{feature.label}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right Column - Image */}
            <div className="relative">
              {/* Main Image */}
              <div className="rounded-2xl overflow-hidden shadow-2xl h-96 md:h-96 bg-gradient-to-br from-blue-100 to-teal-100 dark:from-gray-800 dark:to-gray-700 flex items-center justify-center">
                <img
                  src="/images/hospital/hero-consultation.jpg"
                  alt={t('landing.doctorConsult')}
                  className="w-full h-full object-cover"
                  loading="lazy"
                  onError={(e) => {
                    e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23e5e7eb" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%236b7280" font-size="16"%3E[Image Failed to Load]%3C/text%3E%3C/svg%3E'
                  }}
                />
              </div>

              {/* Floating Card */}
              <div className="absolute -bottom-6 -right-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 max-w-xs border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-teal-100 dark:bg-teal-900/30 rounded-full flex items-center justify-center">
                    <Shield size={20} className="text-teal-600 dark:text-teal-400" />
                  </div>
                  <span className="font-semibold text-navy-900 dark:text-white text-sm">
                    {t('landing.qualityCare')}
                  </span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {t('landing.healthierTomorrow')}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Hospital Image Carousel */}
      <HospitalImageCarousel />

      {/* Benefits Strip */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefitItems.map((item, idx) => {
              const Icon = item.icon
              return (
                <div key={idx} className="flex flex-col items-center text-center">
                  <div className="w-14 h-14 bg-teal-100 dark:bg-teal-900/30 rounded-full flex items-center justify-center mb-4">
                    <Icon size={24} className="text-teal-600 dark:text-teal-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {item.desc}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Watch Demo Modal */}
      <WatchDemoModal
        isOpen={showDemoModal}
        onClose={() => setShowDemoModal(false)}
      />
    </div>
  )
}

export default LandingPage
