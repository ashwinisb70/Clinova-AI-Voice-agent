import React, { useState, useEffect } from 'react'
import { AppLayout } from '../components/AppLayout'
import { useParams, useNavigate } from 'react-router-dom'
import { adminAPI, appointmentAPI } from '../services/api'
import { AlertCircle, ArrowLeft } from 'lucide-react'

interface PatientInfo {
  patient_id: string
  full_name: string
  email: string
  phone: string
  language?: string
  date_of_birth?: string
  gender?: string
  address?: string
  created_at: string
}

interface Appointment {
  appointment_id: string
  patient_name: string
  department: string
  preferred_date: string
  preferred_time: string
  doctor_id?: string
  status: string
  created_at: string
}

export const PatientProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [patient, setPatient] = useState<PatientInfo | null>(null)
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadPatientData = async () => {
      try {
        // Load all patients and find the one with matching ID
        const patientsRes = await adminAPI.getPatients()
        const foundPatient = patientsRes.data.patients?.find((p: any) => p.patient_id === id)

        if (!foundPatient) {
          setError('Patient not found')
          setIsLoading(false)
          return
        }

        setPatient(foundPatient)

        // Load appointments
        const appointmentsRes = await appointmentAPI.getAll()
        const patientAppointments = appointmentsRes.data.appointments?.filter(
          (a: any) => a.patient_id === id
        ) || []
        setAppointments(patientAppointments)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load patient data')
      } finally {
        setIsLoading(false)
      }
    }

    if (id) {
      loadPatientData()
    }
  }, [id])

  if (isLoading) {
    return (
      <AppLayout title="Patient Profile">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (error || !patient) {
    return (
      <AppLayout title="Patient Profile">
        <div className="space-y-4">
          <button
            onClick={() => navigate('/patients')}
            className="flex items-center gap-2 text-teal-600 hover:text-teal-700 text-sm font-medium"
          >
            <ArrowLeft size={16} />
            Back to Patients
          </button>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="text-red-600" size={24} />
            <div>
              <p className="font-medium text-red-900">Error</p>
              <p className="text-red-700 text-sm">{error || 'Patient not found'}</p>
            </div>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout title="Patient Profile">
      <div className="space-y-6">
        {/* Back Button */}
        <button
          onClick={() => navigate('/patients')}
          className="flex items-center gap-2 text-teal-600 hover:text-teal-700 text-sm font-medium"
        >
          <ArrowLeft size={16} />
          Back to Patients
        </button>

        {/* Patient Information */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{patient.full_name}</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-600">Patient ID</p>
              <p className="text-gray-900 mt-1">{patient.patient_id}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Email</p>
              <p className="text-gray-900 mt-1">{patient.email}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Phone</p>
              <p className="text-gray-900 mt-1">{patient.phone}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Language</p>
              <p className="text-gray-900 mt-1">{patient.language || 'Not specified'}</p>
            </div>
            {patient.date_of_birth && (
              <div>
                <p className="text-sm font-medium text-gray-600">Date of Birth</p>
                <p className="text-gray-900 mt-1">{new Date(patient.date_of_birth).toLocaleDateString()}</p>
              </div>
            )}
            {patient.gender && (
              <div>
                <p className="text-sm font-medium text-gray-600">Gender</p>
                <p className="text-gray-900 mt-1">{patient.gender}</p>
              </div>
            )}
            {patient.address && (
              <div className="md:col-span-2">
                <p className="text-sm font-medium text-gray-600">Address</p>
                <p className="text-gray-900 mt-1">{patient.address}</p>
              </div>
            )}
            <div>
              <p className="text-sm font-medium text-gray-600">Member Since</p>
              <p className="text-gray-900 mt-1">{new Date(patient.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        </div>

        {/* Appointments */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Appointments ({appointments.length})</h3>

          {appointments.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Appointment ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Department</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {appointments.map((appt) => (
                  <tr key={appt.appointment_id} className="hover:bg-gray-50">
                    <td className="px-4 py-4 text-sm font-medium text-teal-600">{appt.appointment_id}</td>
                    <td className="px-4 py-4 text-sm text-gray-900">{appt.department}</td>
                    <td className="px-4 py-4 text-sm text-gray-600">{new Date(appt.preferred_date).toLocaleDateString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-600">{appt.preferred_time || '-'}</td>
                    <td className="px-4 py-4 text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        appt.status === 'completed' ? 'bg-green-100 text-green-800' :
                        appt.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                        appt.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {appt.status.charAt(0).toUpperCase() + appt.status.slice(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 text-center py-8">No appointments found</p>
          )}
        </div>
      </div>
    </AppLayout>
  )
}

export default PatientProfile
