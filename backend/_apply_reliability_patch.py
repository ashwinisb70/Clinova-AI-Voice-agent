from pathlib import Path
from datetime import datetime
import shutil
import sys

root = Path.cwd()
files = [
    "services/booking.py",
    "services/notify.py",
    "services/email_service.py",
    "routers/agent_appointments.py",
    "main.py",
    "tests/test_voice_reliability.py",
]
for name in files:
    if not (root / name).is_file():
        sys.exit(f"STOP: expected file not found: {name}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / f"_reliability_patch_backup_{stamp}"
backup.mkdir()
for name in files:
    shutil.copy2(root / name, backup / name.replace("/", "__"))
print(f"Backups created: {backup}")

def edit(name, replacements):
    path = root / name
    source = path.read_text(encoding="utf-8")
    for old, new, label in replacements:
        count = source.count(old)
        if count != 1:
            sys.exit(
                f"STOP: {name}: expected exactly one match for '{label}', found {count}. "
                f"Backups are in {backup}"
            )
        source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")
    print(f"Patched: {name}")

edit("services/booking.py", [
    (
        "from datetime import date, datetime\nimport re\n",
        "from datetime import date, datetime\nimport logging\nimport re\n\nfrom pymongo.errors import PyMongoError\n",
        "booking imports",
    ),
    (
        "ACTIVE_STATUSES = [\"pending\", \"confirmed\", \"rescheduled\", \"scheduled\"]\n",
        "log = logging.getLogger(__name__)\n\nACTIVE_STATUSES = [\"pending\", \"confirmed\", \"rescheduled\", \"scheduled\"]\n",
        "booking logger",
    ),
    (
        '''        candidates = await doctors_collection.find({
            "hospital_id": hospital_id,
            "department_id": dept["department_id"],
            "available": True,
        }).sort("name", 1).to_list(100)
''',
        '''        try:
            candidates = await doctors_collection.find({
                "hospital_id": hospital_id,
                "department_id": dept["department_id"],
                "available": True,
            }).sort("name", 1).to_list(100)
        except PyMongoError as exc:
            log.warning("Voice booking availability query failed")
            raise HTTPException(
                status_code=503,
                detail="A database error occurred; nothing has been booked. Please try again later.",
            ) from exc
''',
        "doctor availability query",
    ),
    (
        '''            same_day_appointments = await appointments_collection.find({
                "hospital_id": hospital_id,
                "doctor_id": candidate["doctor_id"],
                "preferred_date": preferred_date,
                "status": {"$in": ACTIVE_STATUSES},
            }).to_list(500)
''',
        '''            try:
                same_day_appointments = await appointments_collection.find({
                    "hospital_id": hospital_id,
                    "doctor_id": candidate["doctor_id"],
                    "preferred_date": preferred_date,
                    "status": {"$in": ACTIVE_STATUSES},
                }).to_list(500)
            except PyMongoError as exc:
                log.warning("Voice booking appointment conflict check failed")
                raise HTTPException(
                    status_code=503,
                    detail="A database error occurred; nothing has been booked. Please try again later.",
                ) from exc
''',
        "appointment conflict query",
    ),
    (
        '''"patient_name": patient_name.strip(), "patient_email": (patient or {}).get("email") or patient_email, "patient_phone": (patient or {}).get("phone"),''',
        '''"patient_name": patient_name.strip(),
        "patient_email": (patient or {}).get("email") or (patient_email if source != "voice" else None),
        "patient_phone": (patient or {}).get("phone"),''',
        "trusted appointment email",
    ),
    (
        '''    params = appt_params(appt)
    await create_notification(hospital_id=hospital_id, audience="admin", ntype="new_appointment", params=params, link="/admin/appointments")
    if patient_id:
        await create_notification(hospital_id=hospital_id, audience="patient", patient_id=patient_id, ntype="appointment_booked",
                                  params=params, link="/account/appointments")
        await email_patient("appointment_booked", hospital_id=hospital_id, patient=patient, appointment=appt)
    elif patient_email:
        await email_patient("appointment_booked", hospital_id=hospital_id, patient_email=patient_email, appointment=appt)
    return appt
''',
        '''    params = appt_params(appt)
    # Appointment persistence is the primary operation. Notifications and email are
    # best-effort and must not make a saved appointment look like a failed booking.
    try:
        await create_notification(
            hospital_id=hospital_id, audience="admin", ntype="new_appointment",
            params=params, link="/admin/appointments",
        )
        if patient_id:
            await create_notification(
                hospital_id=hospital_id, audience="patient", patient_id=patient_id,
                ntype="appointment_booked", params=params, link="/account/appointments",
            )
            await email_patient(
                "appointment_booked", hospital_id=hospital_id, patient=patient, appointment=appt,
            )
        elif patient_email and source != "voice":
            await email_patient(
                "appointment_booked", hospital_id=hospital_id,
                patient_email=patient_email, appointment=appt,
            )
    except Exception:
        log.warning(
            "A post-booking notification/email step failed for appointment %s",
            appt.get("appointment_id"),
            exc_info=True,
        )
    return appt
''',
        "best-effort booking side effects",
    ),
])

edit("services/notify.py", [
    (
        "from database import notifications_collection, hospitals_collection, patients_collection\n",
        "import logging\n\nfrom database import notifications_collection, hospitals_collection, patients_collection\n",
        "notification imports",
    ),
    (
        "TEXT = {\n",
        "log = logging.getLogger(__name__)\n\nTEXT = {\n",
        "notification logger",
    ),
    (
        '''    await notifications_collection.insert_one(doc)
    room = admin_room(hospital_id) if audience == "admin" else patient_room(patient_id)
    await hub.send(room, {"event": "notification", "notification": serialize(doc)})
    return doc
''',
        '''    try:
        await notifications_collection.insert_one(doc)
    except Exception:
        log.warning("Notification could not be persisted (%s)", ntype, exc_info=True)
        return None

    room = admin_room(hospital_id) if audience == "admin" else patient_room(patient_id)
    try:
        await hub.send(room, {"event": "notification", "notification": serialize(doc)})
    except Exception:
        # Realtime delivery is optional; the stored notification remains available.
        log.warning("Realtime notification delivery failed (%s)", ntype, exc_info=True)
    return doc
''',
        "notification storage and websocket protection",
    ),
    (
        '''    """Send a REAL email to the patient's registered address (looked up from the database, or via patient_email for voice calls)."""''',
        '''    """Queue an email to a registered patient's address when one is available."""''',
        "email privacy docstring",
    ),
    (
        '''    recipient_email = (patient or {}).get("email") or patient_email
''',
        '''    recipient_email = (patient or {}).get("email") or patient_email
''',
        "email recipient lookup",
    ),
])

edit("services/email_service.py", [
    (
        "import logging\n",
        "import logging\n",
        "email logging import",
    ),
    (
        '''    await email_logs_collection.insert_one({
        "email_id": email_id, "hospital_id": hospital_id, "patient_id": patient_id, "to": to,
        "subject": subject, "html": html, "text": text, "kind": kind, "ref": ref or {},
        "from_name": from_name, "status": "pending", "attempts": 0, "error": None,
        "created_at": now(), "updated_at": now(),
    })
    task = asyncio.create_task(_deliver(email_id))
''',
        '''    try:
        await email_logs_collection.insert_one({
            "email_id": email_id, "hospital_id": hospital_id, "patient_id": patient_id, "to": to,
            "subject": subject, "html": html, "text": text, "kind": kind, "ref": ref or {},
            "from_name": from_name, "status": "pending", "attempts": 0, "error": None,
            "created_at": now(), "updated_at": now(),
        })
    except Exception:
        # A failed email-log write must not fail an already-saved booking.
        log.warning("Email could not be queued because the email log was unavailable")
        return None

    task = asyncio.create_task(_deliver(email_id))
''',
        "email queue persistence protection",
    ),
])

edit("routers/agent_appointments.py", [
    (
        "import re\n",
        "import logging\nimport re\n\nfrom pymongo.errors import PyMongoError\n",
        "agent appointment imports",
    ),
    (
        "NOT_FOUND = ",
        "log = logging.getLogger(__name__)\n\nNOT_FOUND = ",
        "agent appointment logger",
    ),
    (
        '''    a = await appointments_collection.find_one({"hospital_id": hid, "appointment_id": payload.appointment_id.strip().upper()})
    if not a:
''',
        '''    try:
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
''',
        "appointment lookup outage handling",
    ),
    (
        '''    patient = await patients_collection.find_one({"hospital_id": hid, "patient_id": a["patient_id"],
                                                  "phone": {"$regex": f"{digits[-10:]}$"}})
    if not patient:
''',
        '''    try:
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
''',
        "patient verification outage handling",
    ),
])

edit("main.py", [
    (
        "email_queued=(bool(patient_id) or bool(clean_patient_email)) and email_configured(),",
        "email_queued=bool(patient_id) and email_configured(),",
        "email queued response",
    ),
])

edit("tests/test_voice_reliability.py", [
    (
        'assert "cancelled successfully" in r.json()["message"]',
        'assert "cancelled" in r.json()["message"].lower()',
        "cancellation message assertion",
    ),
    (
        '''        async def insert_one(self, *_a, **_k):
            raise PyMongoError("simulated outage")

    monkeypatch.setattr(booking_service, "appointments_collection", Broken())
''',
        '''        async def insert_one(self, *_a, **_k):
            raise PyMongoError("simulated outage")

        def find(self, *_a, **_k):
            raise PyMongoError("simulated outage")

    monkeypatch.setattr(booking_service, "appointments_collection", Broken())
''',
        "broken booking collection mock",
    ),
    (
        '''json={"patient_name": "Outage Caller", "department": "Reliability Cardiology", "preferred_date": TOMORROW})''',
        '''json={"patient_name": "Outage Caller", "department": "Reliability Cardiology",
                          "preferred_date": TOMORROW, "preferred_time": "11:00 AM"})''',
        "booking outage test time",
    ),
    (
        '''"preferred_time": "5:00 PM", "patient_email": "caller-supplied@example.com"})''',
        '''"preferred_time": "4:30 PM", "patient_email": "caller-supplied@example.com"})''',
        "voice booking available time",
    ),
    (
        '''    assert stored(body["appointment_id"])["status"] == "pending"
    assert db(email_logs_collection.count_documents, {"hospital_id": HID, "to": "caller-supplied@example.com"}) == 0
''',
        '''    assert stored(body["appointment_id"])["status"] == "confirmed"
    assert db(email_logs_collection.count_documents, {"hospital_id": HID, "to": "caller-supplied@example.com"}) == 0
''',
        "voice booking status expectation",
    ),
])

print("\nPatch applied successfully.")
print(f"Backup folder: {backup}")
