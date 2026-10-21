"""Recurring and walk-in appointments."""
from typing import Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user, require_staff, STAFF_ROLES
from database import appointments_collection, patients_collection, require_db
from services.common import now, short_id, serialize, scoped, parse_date
from services.booking import book, ACTIVE_STATUSES
from services.notify import create_notification, email_patient, appt_params

router = APIRouter(tags=["appointments"])


class BookRecurringRequest(BaseModel):
    patient_id: str
    department: str
    doctor_id: Optional[str] = None
    first_date: str  # YYYY-MM-DD
    appointment_time: str
    frequency: str  # 'daily', 'weekly', 'biweekly', 'monthly'
    occurrences: int  # 1-52


class BookWalkInRequest(BaseModel):
    patient_id: str
    department: str
    doctor_id: Optional[str] = None
    is_emergency: bool = False
    notes: Optional[str] = None


def _generate_recurring_dates(start_date_str: str, frequency: str, occurrences: int) -> list:
    """Generate list of appointment dates based on frequency and occurrences."""
    d = parse_date(start_date_str)
    if not d:
        raise ValueError("Invalid date format")

    dates = [d]
    delta_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'biweekly': timedelta(weeks=2),
        'monthly': timedelta(days=30),  # Approximate
    }

    delta = delta_map.get(frequency)
    if not delta:
        raise ValueError(f"Invalid frequency: {frequency}")

    for _ in range(occurrences - 1):
        d = d + delta
        dates.append(d)

    return dates


@router.post("/book-appointment/recurring")
async def book_recurring(payload: BookRecurringRequest, user: dict = Depends(get_current_user)):
    """Book a series of recurring appointments."""
    require_db()

    if user["role"] not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only staff can create recurring appointments")

    d = parse_date(payload.first_date)
    if not d or d < date.today():
        raise HTTPException(status_code=422, detail="First date must be today or in the future")

    if payload.occurrences < 1 or payload.occurrences > 52:
        raise HTTPException(status_code=422, detail="Occurrences must be between 1 and 52")

    try:
        dates = _generate_recurring_dates(payload.first_date, payload.frequency, payload.occurrences)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    patient = await patients_collection.find_one({"hospital_id": user["hospital_id"], "patient_id": payload.patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient_name = patient["full_name"]
    patient_email = patient.get("email")

    series_id = short_id("REC-")
    created_appts = []
    failed = []

    for appt_date in dates:
        try:
            appt = await book(
                hospital_id=user["hospital_id"],
                patient_id=payload.patient_id,
                patient_name=patient_name,
                patient_email=patient_email,
                department=payload.department,
                doctor_id=payload.doctor_id,
                preferred_date=appt_date.strftime("%Y-%m-%d"),
                preferred_time=payload.appointment_time,
                source="web",
                notes=f"Part of recurring series {series_id}"
            )
            # Mark as part of recurring series
            await appointments_collection.update_one(
                {"appointment_id": appt["appointment_id"]},
                {"$set": {"recurring_series_id": series_id, "recurring_frequency": payload.frequency}}
            )
            created_appts.append(appt)
        except Exception as e:
            failed.append({"date": appt_date.strftime("%Y-%m-%d"), "error": str(e)})

    if not created_appts:
        raise HTTPException(status_code=500, detail="Failed to create any appointments in the series")

    return {
        "success": True,
        "series_id": series_id,
        "created": len(created_appts),
        "failed_count": len(failed),
        "appointments": [serialize(a) for a in created_appts],
        "errors": failed if failed else None
    }


@router.post("/book-appointment/walk-in")
async def book_walk_in(payload: BookWalkInRequest, user: dict = Depends(get_current_user)):
    """Book a walk-in appointment (no specific time required)."""
    require_db()

    if user["role"] not in STAFF_ROLES and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only staff can create walk-in appointments")

    # Use current date and a default queue time
    today = date.today().strftime("%Y-%m-%d")
    queue_time = "09:00"  # Default queue time

    patient = await patients_collection.find_one({"hospital_id": user["hospital_id"], "patient_id": payload.patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient_name = patient["full_name"]

    appt = await book(
        hospital_id=user["hospital_id"],
        patient_id=payload.patient_id,
        patient_name=patient_name,
        patient_email=patient.get("email"),
        department=payload.department,
        doctor_id=payload.doctor_id,
        preferred_date=today,
        preferred_time=queue_time,
        source="walk-in",
        notes=payload.notes
    )

    # Add walk-in specific fields
    priority = "high" if payload.is_emergency else "normal"
    await appointments_collection.update_one(
        {"appointment_id": appt["appointment_id"]},
        {
            "$set": {
                "is_walk_in": True,
                "queue_priority": priority,
                "checked_in_at": now() if payload.is_emergency else None,
                "created_by": user.get("username")
            }
        }
    )

    appt = await appointments_collection.find_one({"appointment_id": appt["appointment_id"]})

    # Notify if emergency
    if payload.is_emergency:
        await create_notification(
            hospital_id=user["hospital_id"],
            audience="admin",
            ntype="emergency_walk_in",
            params={"patient_name": patient_name, "department": payload.department},
            link="/admin/appointments"
        )

    return {"success": True, "appointment": serialize(appt)}
