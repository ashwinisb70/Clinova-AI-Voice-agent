import React from 'react'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import { useToast } from '../context/ToastContext'
import clsx from 'clsx'

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToast()

  return (
    <div className="fixed bottom-4 right-4 z-[9999] space-y-2 max-w-md">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={clsx(
            'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white animate-slide-in',
            toast.type === 'success' && 'bg-green-600',
            toast.type === 'error' && 'bg-red-600',
            toast.type === 'warning' && 'bg-amber-600',
            toast.type === 'info' && 'bg-blue-600'
          )}
        >
          {toast.type === 'success' && <CheckCircle size={20} />}
          {toast.type === 'error' && <AlertCircle size={20} />}
          {toast.type === 'warning' && <AlertCircle size={20} />}
          {toast.type === 'info' && <Info size={20} />}
          
          <span className="flex-1 text-sm">{toast.message}</span>
          
          <button
            onClick={() => removeToast(toast.id)}
            className="text-white/80 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>
      ))}
    </div>
  )
}
