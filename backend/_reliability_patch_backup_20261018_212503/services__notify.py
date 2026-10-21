"""Creates database notifications, pushes them over WebSocket and queues patient emails.
Notifications store a `type` + `params` so the frontend can show them in the user's language;
`title`/`message` are the English fallback."""
from database import notifications_collection, hospitals_collection, patients_collection
from services.common import now, short_id, serialize, pretty_date
from services.realtime import hub, admin_room, patient_room
from services import email_templates
from services.email_service import queue_email

TEXT = {
    "appointment_booked": ("Appointment booked", "Your {department} appointment request for {date} at {time} was received and is pending confirmation."),
    "appointment_pending": ("Appointment pending", "Your appointment {appointment_id} is awaiting hospital confirmation."),
    "appointment_confirmed": ("Appointment confirmed", "Your {department} appointment on {date} at {time} is confirmed."),
    "appointment_completed": ("Appointment completed", "Your appointment {appointment_id} is complete. Your bill is ready."),
    "appointment_cancelled": ("Appointment cancelled", "Your appointment {appointment_id} on {date} at {time} was cancelled."),
    "appointment_rescheduled": ("Appointment rescheduled", "Your appointment {appointment_id} moved to {date} at {time}."),
    "payment_success": ("Payment successful", "Payment of ₹{amount} for invoice {invoice_id} was received."),
    "payment_failed": ("Payment failed", "Payment of ₹{amount} for invoice {invoice_id} failed. You can try again."),
    "payment_refunded": ("Payment refunded", "₹{amount} for invoice {invoice_id} has been refunded."),
    # admin
    "new_appointment": ("New appointment", "{patient_name} booked a {department} appointment for {date} at {time}."),
    "appointment_cancelled_by_patient": ("Appointment cancelled", "{patient_name} cancelled appointment {appointment_id} ({date}, {time})."),
    "appointment_rescheduled_by_patient": ("Appointment rescheduled", "{patient_name} rescheduled appointment {appointment_id} to {date} at {time}."),
    "payment_received": ("Payment received", "Payment of ₹{amount} received from {patient_name} for invoice {invoice_id}."),
    "payment_failed_admin": ("Payment failed", "A payment of ₹{amount} from {patient_name} for invoice {invoice_id} failed."),
    "cash_payment_selected": ("Pay at hospital", "{patient_name} chose to pay ₹{amount} at the hospital for invoice {invoice_id}."),
    "new_escalation": ("Escalation", "{patient_name} needs staff help: {reason}"),
    "contact_message": ("Contact message", "{patient_name} ({email} {phone}) wrote: {message}"),
    "new_patient": ("New patient", "{patient_name} registered a patient account."),
}


def appt_params(a: dict) -> dict:
    return {"appointment_id": a.get("appointment_id"), "department": a.get("department"),
            "doctor": a.get("doctor_name") or "", "date": pretty_date(a.get("preferred_date")),
            "raw_date": a.get("preferred_date"), "time": a.get("preferred_time") or "", "patient_name": a.get("patient_name")}


async def get_hospital(hospital_id: str) -> dict:
    h = await hospitals_collection.find_one({"hospital_id": hospital_id}) if hospitals_collection is not None else None
    return h or {"hospital_id": hospital_id, "name": "City Hospital"}


async def create_notification(*, hospital_id: str, audience: str, ntype: str, params: dict,
                              patient_id: str = None, link: str = None) -> dict:
    if notifications_collection is None:
        return None
    title, msg = TEXT.get(ntype, (ntype, ""))
    safe = {k: ("" if v is None else v) for k, v in params.items()}
    try:
        message = msg.format(**safe)
    except (KeyError, IndexError):
        message = msg
    doc = {"notification_id": short_id("NTF-"), "hospital_id": hospital_id, "audience": audience,
           "patient_id": patient_id, "type": ntype, "params": params, "title": title, "message": message,
           "link": link, "read": False, "created_at": now()}
    await notifications_collection.insert_one(doc)
    room = admin_room(hospital_id) if audience == "admin" else patient_room(patient_id)
    await hub.send(room, {"event": "notification", "notification": serialize(doc)})
    return doc


async def email_patient(kind: str, *, hospital_id: str, patient_id: str = None, patient: dict = None, patient_email: str = None, **ctx):
    """Send a REAL email to the patient's registered address (looked up from the database, or via patient_email for voice calls)."""
    if patient is None and patient_id and patients_collection is not None:
        patient = await patients_collection.find_one({"patient_id": patient_id})
    recipient_email = (patient or {}).get("email") or patient_email
    if not recipient_email:
        return None
    hospital = await get_hospital(hospital_id)
    subject, html, text = email_templates.render(kind, hospital=hospital, patient=patient or {"email": recipient_email}, **ctx)
    ref = {k: (v or {}).get(k2) for k, k2 in (("appointment", "appointment_id"), ("invoice", "invoice_id"), ("payment", "payment_id")) if (v := ctx.get(k))}
    return await queue_email(to=recipient_email, subject=subject, html=html, text=text, kind=kind,
                             hospital_id=hospital_id, patient_id=patient.get("patient_id") if patient else None, ref=ref,
                             from_name=f"MediAssist · {hospital.get('name', 'City Hospital')}")
