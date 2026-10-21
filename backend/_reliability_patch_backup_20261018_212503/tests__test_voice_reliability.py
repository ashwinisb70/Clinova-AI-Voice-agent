"""Reliability checks for the voice-agent workflows and dashboard metrics (isolated tenant RELTEST, in-memory MongoDB).

Covers: persistence after booking/reschedule/cancel, validation failures creating no records, status lookups
reflecting stored state, Asia/Kolkata dates, stale completion metadata cleared on reopen, dashboard counts and
scope, missing or unverified email not blocking a booking, notification/email failures not reporting a saved
booking as failed, database errors returned to the voice agent without claiming success, and tenant isolation.

Run from backend/:  python -m pytest -q tests/test_voice_reliability.py
No real email, notification provider, voice call, or external service is used."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

import main
from auth import create_access_token
from database import (appointments_collection, departments_collection, doctors_collection, email_logs_collection,
                      hospitals_collection)
from routers import agent_appointments
from services import booking as booking_service
from services import common as common_service
from services import email_service
from services import notify as notify_service

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def prevent_real_smtp_in_tests(monkeypatch):
    """Never contact a real mail server from this test module."""
    monkeypatch.setattr(email_service, "_send_smtp", lambda *args, **kwargs: None)

client.__enter__()

KOLKATA = ZoneInfo("Asia/Kolkata")
HID = "RELTEST"
OTHER_HID = "RELOTHER"
AGENT = {"X-Agent-Key": "agent-secret", "X-Hospital-Id": HID}
PHONE = "9000000077"
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()
PATIENT = {"full_name": "Reliability Patient", "email": "reliability.patient@example.com", "phone": PHONE, "password": "TestPass123"}


def db(fn, *args):
    return client.portal.call(fn, *args)


def staff_headers(hid=HID):
    return {"Authorization": f"Bearer {create_access_token('rel-staff', role='staff', hospital_id=hid)}"}


def stored(appt_id, hid=HID):
    return db(appointments_collection.find_one, {"hospital_id": hid, "appointment_id": appt_id})


def count_appointments(**query):
    return db(appointments_collection.count_documents, {"hospital_id": HID, **query})


def insert_appointment(appt_id, **fields):
    now_utc = datetime.now(timezone.utc)
    doc = {"appointment_id": appt_id, "hospital_id": HID, "patient_id": None, "patient_name": "Seeded Patient",
           "department": "Reliability Cardiology", "department_id": "rel-cardio", "doctor_id": None, "doctor_name": None,
           "preferred_date": TOMORROW, "preferred_time": "9:00 AM", "status": "confirmed", "history": [],
           "created_at": now_utc, "updated_at": now_utc}
    doc.update(fields)
    db(appointments_collection.insert_one, doc)
    return appt_id


def verify(appt_id, phone=PHONE):
    return {"appointment_id": appt_id, "phone": phone}


@pytest.fixture(scope="module", autouse=True)
def tenant():
    db(hospitals_collection.insert_one, {"hospital_id": HID, "name": "Reliability Hospital"})
    db(hospitals_collection.insert_one, {"hospital_id": OTHER_HID, "name": "Other Hospital"})
    db(departments_collection.insert_one, {"hospital_id": HID, "department_id": "rel-cardio", "name": "Reliability Cardiology",
                                           "consultation_fee": 300, "active": True})
    db(doctors_collection.insert_one, {"hospital_id": HID, "doctor_id": "dr-rel-1", "name": "Dr Reliability",
                                       "department_id": "rel-cardio", "department": "Reliability Cardiology", "available": True,
                                       "schedule": [
                                           {"day": day, "hours": "9:00 AM - 5:00 PM"}
                                           for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                                       ]})


@pytest.fixture(scope="module")
def patient_token():
    r = client.post("/patients/register", headers={"X-Hospital-Id": HID}, json=PATIENT)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def patient_booking(token, **overrides):
    body = {"patient_name": PATIENT["full_name"], "department": "Reliability Cardiology", "preferred_date": TOMORROW, "preferred_time": "10:30 AM"}
    body.update(overrides)
    r = client.post("/book-appointment", headers={"X-Hospital-Id": HID, "Authorization": f"Bearer {token}"}, json=body)
    assert r.status_code == 200, r.text
    return r.json()["appointment_id"]


# ---------------------------------------------------------------- booking persistence and validation

def test_booking_persists_and_is_listed_for_staff(patient_token):
    appt_id = patient_booking(patient_token, preferred_time="11:15 AM")
    doc = stored(appt_id)
    assert doc is not None and doc["preferred_time"] == "11:15 AM" and doc["status"] == "pending"
    listed = client.get("/appointments", headers=staff_headers(), params={"limit": 200}).json()["appointments"]
    assert appt_id in [a["appointment_id"] for a in listed]


def test_validation_failures_create_no_records():
    before = count_appointments()
    bad_requests = [
        {"patient_name": "Ghost", "department": "Reliability Cardiology", "preferred_date": "2000-01-01"},  # past date
        {"patient_name": "Ghost", "department": "No Such Dept", "preferred_date": TOMORROW},                 # unknown dept
        {"patient_name": "Ghost", "department": "Reliability Cardiology", "preferred_date": "not-a-date"},    # bad date
        {"patient_name": "Ghost", "department": "Reliability Cardiology", "preferred_date": TOMORROW, "doctor_id": "dr-missing"},
    ]
    for body in bad_requests:
        r = client.post("/book-appointment", headers=AGENT, json=body)
        assert r.status_code in (409, 422), (body, r.text)
    assert count_appointments() == before


def test_booking_date_validation_uses_kolkata_today(monkeypatch):
    monkeypatch.setattr(booking_service, "today_local", lambda: date(2031, 3, 10))
    r = client.post("/book-appointment", headers=AGENT,
                    json={"patient_name": "Edge Caller", "department": "Reliability Cardiology", "preferred_date": "2031-03-09"})
    assert r.status_code == 422, r.text  # yesterday in Asia/Kolkata
    r = client.post("/book-appointment", headers=AGENT,
                    json={"patient_name": "Edge Caller", "department": "Reliability Cardiology", "preferred_date": "2031-03-10", "preferred_time": "9:00 AM"})
    assert r.status_code == 200, r.text


def test_local_today_is_asia_kolkata():
    assert common_service.today_local() == datetime.now(KOLKATA).date()


# ---------------------------------------------------------------- voice: reschedule / cancel / status

def test_voice_reschedule_persists_new_date_and_time(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/reschedule", headers=AGENT,
                    json={**verify(appt_id), "preferred_date": NEXT_WEEK, "preferred_time": "4:45 PM"})
    assert r.status_code == 200, r.text
    assert r.json()["appointment"]["preferred_date"] == NEXT_WEEK
    doc = stored(appt_id)
    assert doc["preferred_date"] == NEXT_WEEK and doc["preferred_time"] == "4:45 PM" and doc["status"] == "rescheduled"
    status = client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id)).json()
    assert status["appointment"]["preferred_time"] == "4:45 PM"


def test_voice_cancel_persists_status_and_lookup_reflects_it(patient_token):
    appt_id = patient_booking(patient_token)
    r = client.post("/agent/appointments/cancel", headers=AGENT, json={**verify(appt_id), "confirmed": True, "reason": "test"})
    assert r.status_code == 200 and r.json()["cancelled"] is True, r.text
    assert "cancelled successfully" in r.json()["message"]
    assert stored(appt_id)["status"] == "cancelled"
    assert client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id)).json()["appointment"]["status"] == "cancelled"


def test_status_lookup_returns_current_database_state(patient_token):
    appt_id = patient_booking(patient_token)
    db(appointments_collection.update_one, {"hospital_id": HID, "appointment_id": appt_id}, {"$set": {"preferred_time": "7:20 PM"}})
    body = client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id)).json()
    assert body["appointment"]["preferred_time"] == "7:20 PM"
    assert "7:20 PM" in body["message"]


def test_voice_reschedule_into_taken_doctor_slot_returns_accurate_error(patient_token):
    insert_appointment("RELTAKEN01", doctor_id="dr-rel-1", doctor_name="Dr Reliability", preferred_date=NEXT_WEEK, preferred_time="3:30 PM")
    appt_id = patient_booking(patient_token, preferred_time="8:00 AM")
    db(appointments_collection.update_one, {"hospital_id": HID, "appointment_id": appt_id},
       {"$set": {"doctor_id": "dr-rel-1", "doctor_name": "Dr Reliability"}})
    r = client.post("/agent/appointments/reschedule", headers=AGENT,
                    json={**verify(appt_id), "preferred_date": NEXT_WEEK, "preferred_time": "3:30 PM"})
    assert r.status_code == 409, r.text
    assert "already booked" in r.json()["detail"]
    assert stored(appt_id)["preferred_time"] == "8:00 AM"  # nothing changed


def test_voice_lookup_database_failure_is_reported_as_unconfirmed(monkeypatch, patient_token):
    appt_id = patient_booking(patient_token)

    class Broken:
        async def find_one(self, *_a, **_k):
            raise PyMongoError("simulated outage")

    monkeypatch.setattr(agent_appointments, "appointments_collection", Broken())
    r = client.post("/agent/appointments/status", headers=AGENT, json=verify(appt_id))
    assert r.status_code == 503
    assert "nothing has been confirmed" in r.json()["detail"].lower()


def test_voice_booking_database_failure_is_not_reported_as_booked(monkeypatch):
    class Broken:
        async def find_one(self, *_a, **_k):
            raise PyMongoError("simulated outage")

        async def insert_one(self, *_a, **_k):
            raise PyMongoError("simulated outage")

    monkeypatch.setattr(booking_service, "appointments_collection", Broken())
    before = count_appointments()
    r = client.post("/book-appointment", headers=AGENT,
                    json={"patient_name": "Outage Caller", "department": "Reliability Cardiology", "preferred_date": TOMORROW})
    assert r.status_code == 503, r.text
    assert "nothing has been booked" in r.json()["detail"].lower()
    assert count_appointments() == before


# ---------------------------------------------------------------- notifications and email never falsify success

def test_missing_email_does_not_block_voice_booking_and_unverified_address_gets_no_mail():
    before = db(email_logs_collection.count_documents, {"hospital_id": HID})
    r = client.post("/book-appointment", headers=AGENT,
                    json={"patient_name": "No Email Caller", "department": "Reliability Cardiology", "preferred_date": TOMORROW,
                          "preferred_time": "5:00 PM", "patient_email": "caller-supplied@example.com"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email_queued"] is False
    assert stored(body["appointment_id"])["status"] == "pending"
    assert db(email_logs_collection.count_documents, {"hospital_id": HID, "to": "caller-supplied@example.com"}) == 0
    assert db(email_logs_collection.count_documents, {"hospital_id": HID}) == before


def test_notification_store_failure_does_not_fail_saved_booking(monkeypatch, patient_token):
    class Broken:
        async def insert_one(self, *_a, **_k):
            raise PyMongoError("notification store down")

    monkeypatch.setattr(notify_service, "notifications_collection", Broken())
    appt_id = patient_booking(patient_token, preferred_time="6:30 PM")
    assert stored(appt_id)["status"] == "pending"


def test_email_queue_failure_does_not_fail_saved_booking(monkeypatch, patient_token):
    class Broken:
        async def insert_one(self, *_a, **_k):
            raise PyMongoError("email log down")

    monkeypatch.setattr(email_service, "email_logs_collection", Broken())
    appt_id = patient_booking(patient_token, preferred_time="6:45 PM")
    assert stored(appt_id)["status"] == "pending"


def test_cancel_succeeds_when_notification_store_fails(monkeypatch, patient_token):
    appt_id = patient_booking(patient_token, preferred_time="9:05 AM")

    class Broken:
        async def insert_one(self, *_a, **_k):
            raise PyMongoError("notification store down")

    monkeypatch.setattr(notify_service, "notifications_collection", Broken())
    r = client.post("/agent/appointments/cancel", headers=AGENT, json={**verify(appt_id), "confirmed": True})
    assert r.status_code == 200 and r.json()["cancelled"] is True, r.text
    assert stored(appt_id)["status"] == "cancelled"


# ---------------------------------------------------------------- completion lifecycle and dashboard metrics

def test_completion_date_uses_asia_kolkata_not_utc(monkeypatch, patient_token):
    appt_id = patient_booking(patient_token, preferred_time="10:00 AM")
    # 20:00 UTC on 9 Jan is 01:30 IST on 10 Jan: the local completion date must be 10 Jan.
    monkeypatch.setattr("routers.appointments.now", lambda: datetime(2031, 1, 9, 20, 0, tzinfo=timezone.utc))
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=staff_headers(), json={"status": "completed"})
    assert r.status_code == 200, r.text
    doc = stored(appt_id)
    assert doc["status"] == "completed"
    assert doc["completed_date"] == "2031-01-10"


def test_reopening_completed_appointment_clears_completion_metadata(patient_token):
    appt_id = patient_booking(patient_token, preferred_time="10:20 AM")
    headers = staff_headers()
    assert client.patch(f"/admin/appointments/{appt_id}/status", headers=headers, json={"status": "completed"}).status_code == 200
    assert stored(appt_id)["completed_date"] is not None
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=headers, json={"status": "confirmed"})
    assert r.status_code == 200, r.text
    doc = stored(appt_id)
    assert doc["status"] == "confirmed" and doc["completed_at"] is None and doc["completed_date"] is None


def test_dashboard_counts_follow_records_and_exclude_cancelled():
    today = datetime.now(KOLKATA).date().isoformat()
    headers = staff_headers()
    before = client.get("/admin/summary", headers=headers).json()
    insert_appointment("RELTODAY01", preferred_date=today, preferred_time="9:00 AM", status="confirmed")
    insert_appointment("RELTODAY02", preferred_date=today, preferred_time="9:30 AM", status="cancelled")
    insert_appointment("RELOLD001", preferred_date=today, preferred_time="8:00 AM", status="completed", completed_date="2001-01-01")
    after = client.get("/admin/summary", headers=headers).json()
    # RELTODAY01 (confirmed) + RELOLD001 (completed, scheduled today) count; the cancelled one does not.
    assert after["todays_appointments"] == before["todays_appointments"] + 2
    assert after["total_appointments"] == before["total_appointments"] + 3
    assert after["completed_appointments"] == before["completed_appointments"] + 1
    assert after["completed_today"] == before["completed_today"]  # completed on another date does not count


def test_dashboard_is_scoped_to_hospital():
    assert client.get("/admin/summary", headers=staff_headers(OTHER_HID)).json()["total_appointments"] == 0
    assert client.get("/admin/summary", headers=staff_headers()).json()["total_appointments"] > 0


def test_other_hospital_cannot_see_or_change_voice_booking(patient_token):
    appt_id = patient_booking(patient_token, preferred_time="12:10 PM")
    other = {"X-Agent-Key": "agent-secret", "X-Hospital-Id": OTHER_HID}
    assert client.post("/agent/appointments/status", headers=other, json=verify(appt_id)).status_code == 404
    assert client.post("/agent/appointments/cancel", headers=other, json={**verify(appt_id), "confirmed": True}).status_code == 404
    assert stored(appt_id)["status"] == "pending"

