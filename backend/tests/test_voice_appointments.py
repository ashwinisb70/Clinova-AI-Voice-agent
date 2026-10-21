"""Voice agent appointment workflows (in-memory MongoDB, isolated tenant VOICETEST).
Covers booking, status, reschedule, cancel, staff-only confirm/complete, invalid transitions, unknown
appointments, duplicate retries, and the Bolna webhook. Run from backend/:
    python -m pytest -q tests/test_voice_appointments.py"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import main
from auth import create_access_token
from database import appointments_collection, conversations_collection, departments_collection, doctors_collection, hospitals_collection

client = TestClient(main.app)
client.__enter__()

HID = "VOICETEST"
AGENT = {"X-Agent-Key": "agent-secret", "X-Hospital-Id": HID}
PHONE = "9000000003"
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()
NOT_FOUND = "We could not find an appointment matching those details. Please check the reference number and the phone number on your account."
PATIENT = {"full_name": "Voice Test Patient", "email": "voice.test@example.com", "phone": PHONE, "password": "TestPass123"}


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def staff():
    return create_access_token("voice-staff", role="staff", hospital_id=HID)


def db(fn, query):
    return client.portal.call(fn, query)


@pytest.fixture(scope="module", autouse=True)
def tenant():
    db(hospitals_collection.insert_one, {"hospital_id": HID, "name": "Voice Test Hospital"})
    db(departments_collection.insert_one, {"hospital_id": HID, "department_id": "cardiology", "name": "Cardiology",
                                           "consultation_fee": 500, "active": True})
    db(doctors_collection.insert_one, {"hospital_id": HID, "doctor_id": "dr-voice-1", "name": "Dr Voice",
                                       "department_id": "cardiology", "department": "Cardiology", "available": True})


@pytest.fixture(scope="module")
def patient_token():
    r = client.post("/patients/register", headers={"X-Hospital-Id": HID}, json=PATIENT)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def patient_booking(token, **overrides):
    body = {"patient_name": PATIENT["full_name"], "department": "Cardiology", "preferred_date": TOMORROW, "preferred_time": "10:30 AM"}
    body.update(overrides)
    r = client.post("/book-appointment", headers={"X-Hospital-Id": HID, **bearer(token)}, json=body)
    assert r.status_code == 200, r.text
    return r.json()["appointment_id"]


def voice_booking(conversation_id=None, **overrides):
    body = {"patient_name": "Walk-in Caller", "department": "Cardiology", "preferred_date": TOMORROW, "preferred_time": "3:00 PM"}
    body.update(overrides)
    headers = dict(AGENT)
    if conversation_id:
        headers["X-Conversation-Id"] = conversation_id
    r = client.post("/book-appointment", headers=headers, json=body)
    assert r.status_code == 200, r.text
    return r.json()


def stored(appt_id):
    return db(appointments_collection.find_one, {"hospital_id": HID, "appointment_id": appt_id})


def verify(appt_id, phone=PHONE):
    return {"appointment_id": appt_id, "phone": phone}


# --- booking -----------------------------------------------------------------

def test_voice_booking_returns_saved_pending_reference():
    r = voice_booking(conversation_id="CALL-BOOK-1")
    assert r["status"] == "pending"
    assert stored(r["appointment_id"])["status"] == "pending"
    assert stored(r["appointment_id"])["source"] == "voice"


def test_voice_retry_with_same_conversation_does_not_duplicate():
    first = voice_booking(conversation_id="CALL-RETRY-1")
    second = voice_booking(conversation_id="CALL-RETRY-1")
    assert second["appointment_id"] == first["appointment_id"]
    count = db(appointments_collection.count_documents, {"hospital_id": HID, "conversation_id": "CALL-RETRY-1"})
    assert count == 1


def test_different_conversation_creates_new_booking():
    a = voice_booking(conversation_id="CALL-DIFF-A")
    b = voice_booking(conversation_id="CALL-DIFF-B")
    assert a["appointment_id"] != b["appointment_id"]


def test_voice_booking_requires_agent_key():
    r = client.post("/book-appointment", headers={"X-Hospital-Id": HID},
                    json={"patient_name": "Nobody", "department": "Cardiology", "preferred_date": TOMORROW})
    assert r.status_code == 401


# --- status lookup -----------------------------------------------------------

def test_status_lookup_with_reference_and_registered_phone(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id))
    assert r.status_code == 200, r.text
    assert r.json()["appointment"]["status"] == "pending"
    assert r.json()["appointment"]["appointment_id"] == appt_id
    assert "pending" in r.json()["message"]


def test_status_lookup_accepts_phone_with_country_code_and_spaces(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id, phone="+91 90000 00003"))
    assert r.status_code == 200, r.text


def test_status_lookup_wrong_phone_is_rejected(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id, phone="9111111111"))
    assert r.status_code == 404
    assert r.json()["detail"] == NOT_FOUND


def test_unknown_appointment_reference_is_rejected():
    r = client.post("/agent/appointments/status", headers=AGENT, json=verify("NOSUCHREF"))
    assert r.status_code == 404
    assert r.json()["detail"] == NOT_FOUND


def test_voice_booked_appointment_cannot_be_managed_by_voice():
    booked = voice_booking(conversation_id="CALL-UNLINKED-1")
    r = client.post("/agent/appointments/status", headers=AGENT, json=verify(booked["appointment_id"]))
    assert r.status_code == 409
    assert "not linked to a patient account" in r.json()["detail"]


def test_short_phone_number_is_rejected(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id, phone="123"))
    assert r.status_code == 422


def test_voice_endpoints_require_agent_key(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/status", headers={"X-Hospital-Id": HID}, json=verify(appt_id))
    assert r.status_code == 401
    r = client.post("/agent/appointments/status", headers={"X-Agent-Key": "wrong", "X-Hospital-Id": HID}, json=verify(appt_id))
    assert r.status_code == 401


# --- reschedule --------------------------------------------------------------

def test_reschedule_updates_record_history_and_dashboard_list(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/reschedule", headers=AGENT,
                    json={**verify(appt_id), "preferred_date": NEXT_WEEK, "preferred_time": "11:00 AM"})
    assert r.status_code == 200, r.text
    assert r.json()["appointment"]["preferred_date"] == NEXT_WEEK
    doc = stored(appt_id)
    assert doc["preferred_date"] == NEXT_WEEK and doc["preferred_time"] == "11:00 AM"
    assert doc["status"] == "rescheduled"
    assert any(h["action"] == "rescheduled" for h in doc["history"])
    listed = client.get("/appointments", headers=bearer(staff())).json()["appointments"]
    row = next(a for a in listed if a["appointment_id"] == appt_id)
    assert row["preferred_date"] == NEXT_WEEK and row["status"] == "rescheduled"


def test_reschedule_retry_is_idempotent(patient_token):
    appt_id = patient_booking(patient_token)
    body = {**verify(appt_id), "preferred_date": NEXT_WEEK, "preferred_time": "12:00 PM"}
    assert client.post("/agent/appointments/reschedule", headers=AGENT, json=body).status_code == 200
    assert client.post("/agent/appointments/reschedule", headers=AGENT, json=body).status_code == 200
    doc = stored(appt_id)
    assert len([h for h in doc["history"] if h["action"] == "rescheduled"]) == 1


def test_reschedule_into_doctor_slot_clash_is_rejected(patient_token):
    voice_booking(conversation_id="CALL-CLASH-HOLDER", doctor_id="dr-voice-1", preferred_date=NEXT_WEEK, preferred_time="2:30 PM")
    appt_id = patient_booking(patient_token, doctor_id="dr-voice-1", preferred_date=TOMORROW, preferred_time="9:00 AM")
    r = client.post("/agent/appointments/reschedule", headers=AGENT,
                    json={**verify(appt_id), "preferred_date": NEXT_WEEK, "preferred_time": "2:30 PM"})
    assert r.status_code == 409
    assert stored(appt_id)["preferred_date"] == TOMORROW


def test_reschedule_to_past_date_is_rejected(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/reschedule", headers=AGENT,
                    json={**verify(appt_id), "preferred_date": "2000-01-01", "preferred_time": "10:00 AM"})
    assert r.status_code == 422


def test_reschedule_wrong_phone_changes_nothing(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/reschedule", headers=AGENT,
                    json={**verify(appt_id, phone="9111111111"), "preferred_date": NEXT_WEEK, "preferred_time": "4:00 PM"})
    assert r.status_code == 404
    assert stored(appt_id)["status"] == "pending"


# --- cancel ------------------------------------------------------------------

def test_cancel_requires_confirmation_before_changing_anything(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/cancel", headers=AGENT, json=verify(appt_id))
    assert r.status_code == 200, r.text
    assert r.json()["cancelled"] is False and r.json()["confirmation_required"] is True
    assert stored(appt_id)["status"] == "pending"


def test_confirmed_cancel_updates_record_and_history(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/cancel", headers=AGENT, json={**verify(appt_id), "confirmed": True, "reason": "Caller request"})
    assert r.status_code == 200, r.text
    assert r.json()["cancelled"] is True
    doc = stored(appt_id)
    assert doc["status"] == "cancelled" and doc["cancel_reason"] == "Caller request"
    assert any(h["action"] == "cancelled" for h in doc["history"])


def test_cancel_retry_is_idempotent(patient_token):
    appt_id = patient_booking(patient_token)
    body = {**verify(appt_id), "confirmed": True}
    client.post("/agent/appointments/cancel", headers=AGENT, json=body)
    r = client.post("/agent/appointments/cancel", headers=AGENT, json=body)
    assert r.status_code == 200 and r.json()["cancelled"] is True
    assert len([h for h in stored(appt_id)["history"] if h["action"] == "cancelled"]) == 1


def test_completed_appointment_cannot_be_cancelled_by_voice(patient_token):
    appt_id = patient_booking(patient_token)
    client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "confirmed"})
    client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "completed"})
    r = client.post("/agent/appointments/cancel", headers=AGENT, json={**verify(appt_id), "confirmed": True})
    assert r.status_code == 409
    assert stored(appt_id)["status"] == "completed"


# --- confirm / complete are staff-only ---------------------------------------

def test_voice_agent_cannot_confirm_or_complete(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=AGENT, json={"status": "confirmed"})
    assert r.status_code in (401, 403)
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=AGENT, json={"status": "completed"})
    assert r.status_code in (401, 403)
    assert stored(appt_id)["status"] == "pending"


def test_no_voice_route_exists_for_confirm_or_complete():
    for path in ("/agent/appointments/confirm", "/agent/appointments/complete"):
        r = client.post(path, headers=AGENT, json={"appointment_id": "X", "phone": PHONE})
        assert r.status_code in (404, 405)


# --- Bolna webhook retries ---------------------------------------------------

def test_duplicate_bolna_webhook_creates_one_conversation():
    body = {"id": "EXEC-DUP-1", "status": "completed", "hospital_id": HID, "transcript": "user: hello\nassistant: hi"}
    for _ in range(2):
        r = client.post("/agent/bolna/webhook?key=agent-secret", json=body)
        assert r.status_code == 200, r.text
    count = db(conversations_collection.count_documents, {"hospital_id": HID, "external_id": "EXEC-DUP-1"})
    assert count == 1
