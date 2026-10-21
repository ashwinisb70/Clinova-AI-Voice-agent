import React from 'react'
import clsx from 'clsx'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  icon?: React.ReactNode
  children: React.ReactNode
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', isLoading = false, icon, className, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={clsx(
          'inline-flex items-center justify-center font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
          // Variants
          variant === 'primary' && 'bg-teal-600 text-white hover:bg-teal-700 active:bg-teal-800',
          variant === 'secondary' && 'bg-gray-200 text-gray-900 hover:bg-gray-300 active:bg-gray-400',
          variant === 'danger' && 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800',
          variant === 'ghost' && 'bg-transparent text-gray-700 hover:bg-gray-100 active:bg-gray-200',
          // Sizes
          size === 'sm' && 'px-3 py-2 text-sm gap-2',
          size === 'md' && 'px-4 py-2.5 text-base gap-2',
          size === 'lg' && 'px-6 py-3 text-lg gap-2',
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading...
          </>
        ) : (
          <>
            {icon}
            {props.children}
          </>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'
