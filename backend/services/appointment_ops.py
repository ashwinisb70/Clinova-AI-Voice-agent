"""Cancel and reschedule business rules, shared by the dashboard/patient routes and the voice agent."""
from datetime import date

from fastapi import HTTPException

from database import appointments_collection, invoices_collection
from services.common import now, parse_date, today_local
from services.booking import ACTIVE_STATUSES
from services.notify import create_notification, email_patient, appt_params


def hist(a: dict, action: str, by: str, **extra) -> dict:
    return {"action": action, "by": by, "at": now(), "from_status": a.get("status"), **extra}


async def cancel_appointment(a: dict, reason: str | None, by: str) -> dict:
    if a.get("status") in ("cancelled", "completed"):
        raise HTTPException(status_code=409, detail=f"Appointment is already {a['status']}")
    await appointments_collection.update_one({"_id": a["_id"]}, {"$set": {"status": "cancelled", "cancel_reason": reason,
                                                                          "cancelled_by": by, "updated_at": now()},
                                                                 "$push": {"history": hist(a, "cancelled", by, reason=reason)}})
    if a.get("invoice_id"):
        await invoices_collection.update_one({"invoice_id": a["invoice_id"], "status": "pending"}, {"$set": {"status": "cancelled", "updated_at": now()}})
    a = await appointments_collection.find_one({"_id": a["_id"]})
    p = appt_params(a)
    hid = a["hospital_id"]
    if by == "patient":
        await create_notification(hospital_id=hid, audience="admin", ntype="appointment_cancelled_by_patient", params=p, link="/admin/appointments")
    if a.get("patient_id"):
        await create_notification(hospital_id=hid, audience="patient", patient_id=a["patient_id"], ntype="appointment_cancelled", params=p, link="/account/appointments")
        await email_patient("appointment_cancelled" if by == "patient" else "appointment_cancelled_by_hospital", hospital_id=hid,
                            patient_id=a["patient_id"], appointment=a, extra={"reason": reason})
    return a


async def reschedule_appointment(a: dict, new_date: str, new_time: str, by: str) -> dict:
    if a.get("status") in ("cancelled", "completed"):
        raise HTTPException(status_code=409, detail=f"A {a['status']} appointment can't be rescheduled")
    d = parse_date(new_date)
    if not d or d < today_local():
        raise HTTPException(status_code=422, detail="Please choose today or a future date")
    if new_date == a.get("preferred_date") and new_time == a.get("preferred_time"):
        raise HTTPException(status_code=422, detail="Choose a different date or time")
    if a.get("doctor_id"):
        clash = await appointments_collection.find_one({"hospital_id": a["hospital_id"], "doctor_id": a["doctor_id"],
                                                        "appointment_id": {"$ne": a["appointment_id"]},
                                                        "preferred_date": new_date, "preferred_time": new_time,
                                                        "status": {"$in": ACTIVE_STATUSES}})
        if clash:
            raise HTTPException(status_code=409, detail="This time slot is already booked for the doctor. Please choose another time.")
    previous = {"preferred_date": a.get("preferred_date"), "preferred_time": a.get("preferred_time")}
    new = {"preferred_date": new_date, "preferred_time": new_time}
    new_status = "rescheduled" if by == "patient" else "confirmed"
    await appointments_collection.update_one({"_id": a["_id"]}, {"$set": {**new, "status": new_status, "updated_at": now()},
                                                                 "$push": {"history": hist(a, "rescheduled", by, previous=previous, new=new)}})
    a = await appointments_collection.find_one({"_id": a["_id"]})
    p = appt_params(a)
    hid = a["hospital_id"]
    if by == "patient":
        await create_notification(hospital_id=hid, audience="admin", ntype="appointment_rescheduled_by_patient", params=p, link="/admin/appointments")
    if a.get("patient_id"):
        await create_notification(hospital_id=hid, audience="patient", patient_id=a["patient_id"], ntype="appointment_rescheduled", params=p, link="/account/appointments")
        await email_patient("appointment_rescheduled" if by == "patient" else "appointment_rescheduled_by_hospital", hospital_id=hid,
                            patient_id=a["patient_id"], appointment=a, previous=previous)
    return a

