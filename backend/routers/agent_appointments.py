"""Voice agent appointment tools: status, reschedule, cancel.

Authenticated with the agent key (X-Agent-Key). The caller is verified by the appointment reference plus the
phone number on the registered patient account that owns it. Only appointments linked to a patient account
can be changed by voice. Confirm and complete are staff-only and have no voice endpoint."""
import logging
import re

from pymongo.errors import PyMongoError
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator

from database import appointments_collection, patients_collection, require_db
from routers.conversations import record_tool_event
from services.appointment_ops import cancel_appointment, reschedule_appointment
from services.common import require_agent, request_hospital_id

router = APIRouter(prefix="/agent/appointments", tags=["agent-appointments"], dependencies=[Depends(require_agent)])

log = logging.getLogger(__name__)

NOT_FOUND = "We could not find an appointment matching those details. Please check the reference number and the phone number on your account."
UNLINKED = "This appointment is not linked to a patient account, so it cannot be changed by phone. Please contact the hospital."


class VerifyRequest(BaseModel):
    appointment_id: str
    phone: str


class RescheduleRequest(VerifyRequest):
    preferred_date: str
    preferred_time: str

    @field_validator("preferred_time")
    @classmethod
    def _time_present(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Please give the new appointment time, for example 10:30 AM.")
        return v


class CancelRequest(VerifyRequest):
    confirmed: bool = False
    reason: Optional[str] = None


def _summary(a: dict) -> dict:
    return {k: a.get(k) for k in ("appointment_id", "status", "patient_name", "department", "doctor_name", "preferred_date", "preferred_time")}


def _describe(a: dict) -> str:
    when = f"{a.get('preferred_date')} at {a.get('preferred_time') or 'the scheduled time'}"
    return f"Your {a.get('department')} appointment on {when} is {a.get('status')}."


async def _verified(hid: str, payload: VerifyRequest) -> dict:
    require_db()
    digits = re.sub(r"\D", "", payload.phone or "")
    if len(digits) < 10:
        raise HTTPException(status_code=422, detail="Please give the 10-digit phone number on your account.")
    try:
        a = await appointments_collection.find_one({
            "hospital_id": hid,
            "appointment_id": payload.appointment_id.strip().upper(),
        })
    except PyMongoError as exc:
        log.warning("Voice appointment lookup failed")
        raise HTTPException(
            status_code=503,
            detail="We cannot verify the appointment right now; nothing has been confirmed. Please try again later.",
        ) from exc
    if not a:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    if not a.get("patient_id"):
        raise HTTPException(status_code=409, detail=UNLINKED)
    try:
        patient = await patients_collection.find_one({
            "hospital_id": hid,
            "patient_id": a["patient_id"],
            "phone": {"$regex": f"{digits[-10:]}$"},
        })
    except PyMongoError as exc:
        log.warning("Voice patient verification lookup failed")
        raise HTTPException(
            status_code=503,
            detail="We cannot verify the appointment right now; nothing has been confirmed. Please try again later.",
        ) from exc
    if not patient:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return a


@router.post("/status")
async def check_status(payload: VerifyRequest, hid: str = Depends(request_hospital_id)):
    a = await _verified(hid, payload)
    return {"appointment": _summary(a), "message": _describe(a)}


@router.post("/reschedule")
async def reschedule(payload: RescheduleRequest, hid: str = Depends(request_hospital_id),
                     x_conversation_id: Optional[str] = Header(default=None)):
    a = await _verified(hid, payload)
    already_there = a.get("status") == "rescheduled" and (a.get("preferred_date"), a.get("preferred_time")) == (payload.preferred_date, payload.preferred_time)
    updated = a if already_there else await reschedule_appointment(a, payload.preferred_date, payload.preferred_time, by="patient")
    await record_tool_event(hid, x_conversation_id, f"Appointment {a['appointment_id']} rescheduled by voice to {payload.preferred_date} {payload.preferred_time}")
    return {"appointment": _summary(updated), "message": _describe(updated)}


@router.post("/cancel")
async def cancel(payload: CancelRequest, hid: str = Depends(request_hospital_id),
                 x_conversation_id: Optional[str] = Header(default=None)):
    a = await _verified(hid, payload)
    if a.get("status") == "cancelled":
        return {"appointment": _summary(a), "cancelled": True, "message": "This appointment is already cancelled."}
    if not payload.confirmed:
        return {"appointment": _summary(a), "cancelled": False, "confirmation_required": True,
                "message": f"Ask the caller to confirm cancelling the {a.get('department')} appointment on {a.get('preferred_date')} at {a.get('preferred_time') or 'the scheduled time'}."}
    updated = await cancel_appointment(a, payload.reason, by="patient")
    await record_tool_event(hid, x_conversation_id, f"Appointment {a['appointment_id']} cancelled by voice")
    return {"appointment": _summary(updated), "cancelled": True, "message": "Your appointment has been cancelled."}
