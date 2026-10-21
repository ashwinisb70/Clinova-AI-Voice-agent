from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BookAppointmentRequest(BaseModel):
    patient_name: str
    department: str
    preferred_date: str
    preferred_time: Optional[str] = None
    # optional additions (existing callers can ignore them)
    doctor_id: Optional[str] = None
    notes: Optional[str] = None
    patient_email: Optional[str] = None  # For voice/Bolna appointments


class BookAppointmentResponse(BaseModel):
    success: bool
    message: str
    appointment_id: Optional[str] = None
    status: Optional[str] = None
    invoice_id: Optional[str] = None
    email_queued: Optional[bool] = None  # True when a booking email was queued for delivery (SMTP configured)


class FAQRequest(BaseModel):
    question: str
    topic: Optional[str] = None


class FAQResponse(BaseModel):
    success: bool
    answer: str


class EscalateRequest(BaseModel):
    patient_name: Optional[str] = None
    reason: str
    urgency: Optional[str] = "routine"


class EscalateResponse(BaseModel):
    success: bool
    message: str
    escalation_id: Optional[str] = None


class CallLogEntry(BaseModel):
    tool_name: str
    request_data: dict
    response_data: dict
    timestamp: datetime = None
