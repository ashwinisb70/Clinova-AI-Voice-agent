import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8002'
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ==================== STAFF AUTH ====================

export const authAPI = {
  register: (data: { username: string; password: string }) => 
    api.post('/auth/register', data),
  login: (data: { username: string; password: string }) => 
    api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

// ==================== PATIENTS (Patient Portal) ====================

export const patientAPI = {
  register: (data: any) => api.post('/patients/register', data),
  login: (data: any) => api.post('/patients/login', data),
  me: () => api.get('/patients/me'),
  updateProfile: (data: any) => api.put('/patients/me', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/patients/me/password', data),
  forgotPassword: (email: string) => api.post('/patients/forgot-password', { email }),
  resetPassword: (token: string, password: string) =>
    api.post('/patients/reset-password', { token, password }),
}

// ==================== HOSPITAL DATA ====================

export const hospitalAPI = {
  getDetails: () => api.get('/hospital'),
  updateDetails: (data: any) => api.put('/admin/hospital', data),
}

// ==================== DEPARTMENTS ====================

export const departmentAPI = {
  getAll: () => api.get('/departments'),
  getAdminList: () => api.get('/admin/departments'),
  create: (data: any) => api.post('/admin/departments', data),
  update: (deptId: string, data: any) => api.put(`/admin/departments/${deptId}`, data),
  delete: (deptId: string) => api.delete(`/admin/departments/${deptId}`),
}

// ==================== DOCTORS ====================

export const doctorAPI = {
  getAll: (deptId?: string) => api.get('/doctors', { params: { department_id: deptId } }),
  getById: (docId: string) => api.get(`/doctors/${docId}`),
  create: (data: any) => api.post('/admin/doctors', data),
  update: (docId: string, data: any) => api.put(`/admin/doctors/${docId}`, data),
  delete: (docId: string) => api.delete(`/admin/doctors/${docId}`),
}

// ==================== APPOINTMENTS ====================

export const appointmentAPI = {
  getAll: (status?: string) => api.get('/appointments', { params: { status } }),
  getById: (apptId: string) => api.get(`/appointments/${apptId}`),
  book: (data: any) => api.post('/book-appointment', data),
  staffBook: (data: any) => api.post('/admin/appointments/book', data),
  bookRecurring: (data: any) => api.post('/book-appointment/recurring', data),
  bookWalkIn: (data: any) => api.post('/book-appointment/walk-in', data),
  cancel: (apptId: string, reason?: string) =>
    api.post(`/appointments/${apptId}/cancel`, { reason }),
  reschedule: (apptId: string, data: { preferred_date: string; preferred_time: string }) =>
    api.post(`/appointments/${apptId}/reschedule`, data),
  updateStatus: (apptId: string, status: string) =>
    api.patch(`/admin/appointments/${apptId}/status`, { status }),
}

// ==================== INVOICES ====================

export const invoiceAPI = {
  getAll: (status?: string) => api.get('/invoices', { params: { status } }),
  getById: (invId: string) => api.get(`/invoices/${invId}`),
  create: (data: any) => api.post('/admin/invoices', data),
  update: (invId: string, items: any[]) => 
    api.patch(`/admin/invoices/${invId}`, { items }),
}

// ==================== PAYMENTS ====================

export const paymentAPI = {
  getAll: () => api.get('/payments'),
  getById: (payId: string) => api.get(`/payments/${payId}`),
  createOrder: (data: any) => api.post('/payments/order', data),
  verify: (data: any) => api.post('/payments/verify', data),
  reportFailed: (data: any) => api.post('/payments/failed', data),
  markPaid: (payId: string) => api.post(`/admin/payments/${payId}/mark-paid`),
  refund: (payId: string, amount?: number, reason?: string) =>
    api.post(`/admin/payments/${payId}/refund`, { amount, reason }),
}

// ==================== NOTIFICATIONS ====================

export const notificationAPI = {
  getAll: (unreadOnly?: boolean, limit?: number) =>
    api.get('/notifications', { params: { unread_only: unreadOnly, limit } }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAsRead: (notifId: string) => api.post(`/notifications/${notifId}/read`),
  markAllAsRead: () => api.post('/notifications/read-all'),
}

// ==================== EMAIL ====================

export const emailAPI = {
  getLogs: () => api.get('/admin/email-logs'),
  retry: (logId: string) => api.post(`/admin/email-logs/${logId}/retry`),
}

// ==================== DASHBOARD ====================

export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
  getAdminSummary: () => api.get('/admin/summary'),
  getAnalytics: (days?: number) => api.get('/admin/analytics', { params: { days } }),
}

// ==================== ESCALATIONS ====================

export const escalationAPI = {
  getAll: () => api.get('/escalations'),
  escalate: (data: any) => api.post('/escalate', data),
  update: (escalationId: string, status: 'pending' | 'resolved') =>
    api.patch(`/admin/escalations/${escalationId}`, { status }),
}

// ==================== ADMIN ====================

export const adminAPI = {
  getSummary: () => api.get('/admin/summary'),
  getAnalytics: (days?: number) => api.get('/admin/analytics', { params: { days } }),
  getPatients: (query?: string) => api.get('/admin/patients', { params: { q: query } }),
  createPatient: (data: { full_name: string; email: string; phone: string }) => api.post('/admin/patients', data),
  getEmailLogs: (status?: string) => api.get('/admin/email-logs', { params: { status } }),
  retryEmail: (emailId: string) => api.post(`/admin/email-logs/${emailId}/retry`),
}

// ==================== HEALTH ====================

export const healthAPI = {
  check: () => api.get('/health'),
}

export default api
