import React, { useState, useEffect, useRef } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

interface CarouselSlide {
  id: string
  image: string
  alt: string
  titleKey: string
  descKey: string
}

export const HospitalImageCarousel: React.FC = () => {
  const { t } = useLanguage()
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isHovering, setIsHovering] = useState(false)
  const [touchStart, setTouchStart] = useState(0)
  const [touchEnd, setTouchEnd] = useState(0)
  const autoSlideRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const slides: CarouselSlide[] = [
    {
      id: 'slide-1',
      image: '/images/hospital/carousel-hospital-interior.jpg',
      alt: t('carousel.slide1'),
      titleKey: 'carousel.slide1',
      descKey: 'carousel.slide1Desc',
    },
    {
      id: 'slide-2',
      image: '/images/hospital/carousel-medical-team.jpg',
      alt: t('carousel.slide2'),
      titleKey: 'carousel.slide2',
      descKey: 'carousel.slide2Desc',
    },
    {
      id: 'slide-3',
      image: '/images/hospital/carousel-patient-room.jpg',
      alt: t('carousel.slide3'),
      titleKey: 'carousel.slide3',
      descKey: 'carousel.slide3Desc',
    },
    {
      id: 'slide-4',
      image: '/images/hospital/carousel-digital-healthcare.jpg',
      alt: t('carousel.slide4'),
      titleKey: 'carousel.slide4',
      descKey: 'carousel.slide4Desc',
    },
  ]

  const startAutoSlide = () => {
    if (autoSlideRef.current) {
      clearTimeout(autoSlideRef.current)
    }

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const interval = prefersReducedMotion ? 8000 : 4500

    autoSlideRef.current = setTimeout(() => {
      if (!isHovering) {
        setCurrentSlide((prev) => (prev + 1) % slides.length)
      }
    }, interval)
  }

  useEffect(() => {
    startAutoSlide()
    return () => {
      if (autoSlideRef.current) {
        clearTimeout(autoSlideRef.current)
      }
    }
  }, [currentSlide, isHovering, slides.length])

  const goToSlide = (index: number) => {
    setCurrentSlide(index % slides.length)
  }

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length)
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX)
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    setTouchEnd(e.changedTouches[0].clientX)
    handleSwipe()
  }

  const handleSwipe = () => {
    if (touchStart - touchEnd > 50) {
      nextSlide()
    }
    if (touchStart - touchEnd < -50) {
      prevSlide()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      prevSlide()
    } else if (e.key === 'ArrowRight') {
      nextSlide()
    }
  }

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-900">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-navy-900 dark:text-white mb-4">
            {t('carousel.title')}
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            {t('carousel.subtitle')}
          </p>
        </div>

        {/* Carousel Container */}
        <div
          ref={containerRef}
          className="relative rounded-2xl overflow-hidden shadow-2xl bg-gray-100 dark:bg-gray-800"
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
          onKeyDown={handleKeyDown}
          role="region"
          aria-label="Hospital facilities carousel"
          tabIndex={0}
        >
          {/* Slides */}
          <div className="relative h-96 sm:h-[500px] md:h-[550px] lg:h-96 overflow-hidden">
            {slides.map((slide, index) => (
              <div
                key={slide.id}
                className={`absolute inset-0 transition-opacity duration-500 ease-in-out ${
                  index === currentSlide ? 'opacity-100' : 'opacity-0'
                }`}
              >
                {/* Image */}
                <img
                  src={slide.image}
                  alt={slide.alt}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600"%3E%3Crect fill="%23e5e7eb" width="1200" height="600"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%236b7280" font-size="24"%3E[Image Failed to Load]%3C/text%3E%3C/svg%3E'
                  }}
                />

                {/* Overlay and Caption */}
                <div className="absolute inset-0 bg-black/40 flex flex-col justify-end p-6 sm:p-8 md:p-12">
                  <div className="text-white">
                    <h3 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 sm:mb-3">
                      {t(slide.titleKey)}
                    </h3>
                    <p className="text-base sm:text-lg md:text-xl text-gray-100">
                      {t(slide.descKey)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Previous Button */}
          <button
            onClick={prevSlide}
            aria-label={t('carousel.prev')}
            className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-full p-2 sm:p-3 transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <ChevronLeft size={24} />
          </button>

          {/* Next Button */}
          <button
            onClick={nextSlide}
            aria-label={t('carousel.next')}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-full p-2 sm:p-3 transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <ChevronRight size={24} />
          </button>

          {/* Navigation Dots */}
          <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-10 flex gap-2">
            {slides.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                aria-label={`Go to slide ${index + 1}`}
                className={`rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                  index === currentSlide
                    ? 'bg-white dark:bg-gray-200 w-8 h-3'
                    : 'bg-white/60 dark:bg-gray-500 w-3 h-3 hover:bg-white/80 dark:hover:bg-gray-400'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Slide Counter */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {currentSlide + 1} / {slides.length}
          </p>
        </div>
      </div>
    </section>
  )
}

export default HospitalImageCarousel
