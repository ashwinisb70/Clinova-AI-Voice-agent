"""Appointment detail / cancel / reschedule / status. (Booking + listing stay in main.py.)"""
from typing import Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user, require_staff, STAFF_ROLES
from database import appointments_collection, patients_collection, require_db
from services.common import now, serialize, scoped
from services.booking import book
from services.appointment_ops import cancel_appointment, reschedule_appointment
from services.notify import create_notification, email_patient, appt_params

router = APIRouter(tags=["appointments"])

STATUSES = ("pending", "confirmed", "cancelled", "rescheduled", "completed")


async def load_for(user: dict, appointment_id: str) -> dict:
    require_db()
    extra = {"appointment_id": appointment_id}
    if user["role"] == "patient":
        extra["patient_id"] = user["username"]
    elif user["role"] not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Not allowed")
    a = await appointments_collection.find_one(scoped(user["hospital_id"], extra))
    if not a:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return a


@router.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: str, user: dict = Depends(get_current_user)):
    return {"appointment": serialize(await load_for(user, appointment_id))}


class CancelRequest(BaseModel):
    reason: Optional[str] = None


class RescheduleRequest(BaseModel):
    preferred_date: str
    preferred_time: str


class StatusRequest(BaseModel):
    status: str


def _hist(a, action, by, **extra):
    return {"action": action, "by": by, "at": now(), "from_status": a.get("status"), **extra}


@router.post("/appointments/{appointment_id}/cancel")
async def cancel(appointment_id: str, payload: CancelRequest, user: dict = Depends(get_current_user)):
    a = await load_for(user, appointment_id)
    by = "patient" if user["role"] == "patient" else "hospital"
    a = await cancel_appointment(a, payload.reason, by)
    return {"appointment": serialize(a)}


@router.post("/appointments/{appointment_id}/reschedule")
async def reschedule(appointment_id: str, payload: RescheduleRequest, user: dict = Depends(get_current_user)):
    a = await load_for(user, appointment_id)
    by = "patient" if user["role"] == "patient" else "hospital"
    a = await reschedule_appointment(a, payload.preferred_date, payload.preferred_time, by)
    return {"appointment": serialize(a)}


@router.patch("/admin/appointments/{appointment_id}/status")
async def set_status(appointment_id: str, payload: StatusRequest, user: dict = Depends(require_staff)):
    status = payload.status.lower()
    if status not in ("pending", "confirmed", "completed"):
        raise HTTPException(status_code=422, detail="Use the cancel / reschedule endpoints for those changes")
    a = await load_for(user, appointment_id)
    if a.get("status") == status:
        return {"appointment": serialize(a)}  # no change → no duplicate email
    if a.get("status") == "cancelled":
        raise HTTPException(status_code=409, detail="A cancelled appointment can't be changed")
    update_doc = {"status": status, "updated_at": now()}
    if status == "completed":
        completed_at = now()
        completed_date = completed_at.astimezone(pytz.timezone("Asia/Kolkata")).date().isoformat()
        update_doc.update({"completed_at": completed_at, "completed_date": completed_date})
    elif a.get("status") == "completed":
        update_doc.update({"completed_at": None, "completed_date": None})
    await appointments_collection.update_one({"_id": a["_id"]}, {"$set": update_doc,
                                                                 "$push": {"history": _hist(a, status, "hospital")}})
    a = await appointments_collection.find_one({"_id": a["_id"]})
    if a.get("patient_id"):
        ntype = f"appointment_{status}"
        await create_notification(hospital_id=user["hospital_id"], audience="patient", patient_id=a["patient_id"], ntype=ntype,
                                  params=appt_params(a), link="/account/appointments")
        await email_patient(ntype, hospital_id=user["hospital_id"], patient_id=a["patient_id"], appointment=a)
    return {"appointment": serialize(a)}


class StaffBookRequest(BaseModel):
    patient_id: str
    department: str
    doctor_id: Optional[str] = None
    preferred_date: str
    preferred_time: Optional[str] = None
    notes: Optional[str] = None


@router.post("/admin/appointments/book")
async def staff_book(payload: StaffBookRequest, user: dict = Depends(require_staff)):
    require_db()
    patient = await patients_collection.find_one({"hospital_id": user["hospital_id"], "patient_id": payload.patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    appt = await book(hospital_id=user["hospital_id"], patient_id=payload.patient_id, patient_name=patient["full_name"],
                      patient_email=patient.get("email"), department=payload.department, doctor_id=payload.doctor_id,
                      preferred_date=payload.preferred_date, preferred_time=payload.preferred_time,
                      source="staff", notes=payload.notes)
    return {"success": True, "appointment": serialize(appt)}
