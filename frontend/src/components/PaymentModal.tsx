import React, { useState, useCallback } from 'react'
import { X, AlertCircle } from 'lucide-react'
import { paymentAPI } from '../services/api'
import { useToast } from '../context/ToastContext'

interface PaymentModalProps {
  invoiceId: string
  invoiceAmount: number
  patientName: string
  onSuccess: () => void
  onClose: () => void
}

export const PaymentModal: React.FC<PaymentModalProps> = ({
  invoiceId,
  invoiceAmount,
  patientName,
  onSuccess,
  onClose,
}) => {
  const { addToast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)

  const handlePaymentClick = useCallback(async () => {
    if (isLoading || isVerifying) return

    setIsLoading(true)
    setError(null)

    try {
      // Step 1: Create order on backend
      const orderResponse = await paymentAPI.createOrder({
        invoice_id: invoiceId,
        method: 'upi',
        upi_app: 'gpay',
      })

      const orderData = orderResponse.data

      // Handle cash payment (should not reach checkout, but handle it)
      if (orderData.mode === 'cash') {
        setError('Please choose an online payment method for this flow')
        setIsLoading(false)
        return
      }

      // Step 2: Check if Razorpay is loaded
      if (typeof (window as any).Razorpay === 'undefined') {
        throw new Error('Razorpay payment gateway is not available. Please refresh the page and try again.')
      }

      // Step 3: Initialize Razorpay Checkout
      const options = {
        key: orderData.key_id,
        order_id: orderData.order_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: orderData.name,
        description: orderData.description,
        prefill: orderData.prefill,
        handler: async (response: any) => {
          await verifyPayment(response)
        },
        modal: {
          ondismiss: () => {
            setIsLoading(false)
          },
        },
      }

      const rzp = new (window as any).Razorpay(options)
      rzp.open()
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create payment order'
      setError(errorMsg)
      addToast(errorMsg, 'error')
      setIsLoading(false)
    }
  }, [invoiceId, isLoading, isVerifying, addToast])

  const verifyPayment = useCallback(
    async (response: any) => {
      setIsVerifying(true)
      setError(null)

      try {
        // Step 4: Verify payment with backend
        const verifyResponse = await paymentAPI.verify({
          razorpay_order_id: response.razorpay_order_id,
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_signature: response.razorpay_signature,
        })

        const payment = verifyResponse.data.payment

        if (payment.status === 'paid') {
          addToast('Payment successful! Your invoice has been marked as paid.', 'success')
          setIsLoading(false)
          setIsVerifying(false)
          onSuccess()
        } else if (payment.status === 'failed') {
          throw new Error('Payment was rejected. Please try again with a different payment method.')
        } else {
          throw new Error('Payment is being processed. Please wait for confirmation.')
        }
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || err.message || 'Payment verification failed'
        setError(errorMsg)
        addToast(errorMsg, 'error')
        setIsVerifying(false)
        setIsLoading(false)
      }
    },
    [onSuccess, addToast]
  )

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Payment Checkout</h3>
          <button
            onClick={onClose}
            disabled={isLoading || isVerifying}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {/* Invoice Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <span className="text-sm text-gray-600">Invoice Amount</span>
              <span className="text-2xl font-bold text-teal-600">₹{invoiceAmount.toFixed(2)}</span>
            </div>
            <div className="text-xs text-gray-500">
              <p>Patient: {patientName}</p>
              <p>Invoice ID: {invoiceId}</p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-3">
              <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Success State */}
          {isVerifying && !error && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-3">
              <div className="text-blue-600 flex-shrink-0 mt-0.5">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
              </div>
              <p className="text-sm text-blue-700">Verifying your payment...</p>
            </div>
          )}

          {/* Payment Methods Info */}
          {!isLoading && !isVerifying && (
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs text-blue-700">
                <strong>Test Mode:</strong> You can use test UPI with any amount. The payment will be processed through Razorpay's test environment.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center gap-3">
          <button
            onClick={onClose}
            disabled={isLoading || isVerifying}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handlePaymentClick}
            disabled={isLoading || isVerifying}
            className="flex-1 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm flex items-center justify-center gap-2"
          >
            {isLoading || isVerifying ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Processing...
              </>
            ) : (
              <>Pay ₹{invoiceAmount.toFixed(2)}</>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default PaymentModal
