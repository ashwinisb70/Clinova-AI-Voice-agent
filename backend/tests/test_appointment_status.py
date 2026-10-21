"""Appointment status workflow: pending by default, staff confirm/complete, patients and other hospitals blocked.
Runs against in-memory MongoDB in its own tenant (STATUSTEST). Run from backend/:
    python -m pytest -q tests/test_appointment_status.py"""
from datetime import date, datetime, timedelta

import pytz

import pytest
from fastapi.testclient import TestClient

import main
from auth import create_access_token
from database import hospitals_collection, departments_collection

client = TestClient(main.app)
client.__enter__()

HID = "STATUSTEST"
OTHER_HID = "STATUSOTHER"
HDR = {"X-Hospital-Id": HID}
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
PATIENT = {"full_name": "Status Test Patient", "email": "status.test@example.com", "phone": "9000000002", "password": "TestPass123"}


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def staff(hid=HID):
    return create_access_token("status-staff", role="staff", hospital_id=hid)


@pytest.fixture(scope="module", autouse=True)
def tenant():
    client.portal.call(hospitals_collection.insert_one, {"hospital_id": HID, "name": "Status Test Hospital"})
    client.portal.call(departments_collection.insert_one,
                       {"hospital_id": HID, "department_id": "cardiology", "name": "Cardiology", "consultation_fee": 500, "active": True})


@pytest.fixture(scope="module")
def patient_token():
    r = client.post("/patients/register", headers=HDR, json=PATIENT)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def new_booking(token):
    r = client.post("/book-appointment", headers={**HDR, **bearer(token)},
                    json={"patient_name": PATIENT["full_name"], "department": "Cardiology",
                          "preferred_date": TOMORROW, "preferred_time": "10:30 AM"})
    assert r.status_code == 200, r.text
    return r.json()["appointment_id"]


def status_of(appt_id):
    return client.get(f"/appointments/{appt_id}", headers=bearer(staff())).json()["appointment"]["status"]


def test_patient_booking_starts_as_pending(patient_token):
    appt_id = new_booking(patient_token)
    assert status_of(appt_id) == "pending"


def test_staff_can_confirm_pending_appointment(patient_token):
    appt_id = new_booking(patient_token)
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "confirmed"})
    assert r.status_code == 200, r.text
    assert r.json()["appointment"]["status"] == "confirmed"
    assert status_of(appt_id) == "confirmed"


def test_staff_can_complete_confirmed_appointment(patient_token):
    appt_id = new_booking(patient_token)
    client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "confirmed"})
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "completed"})
    assert r.status_code == 200, r.text
    assert status_of(appt_id) == "completed"


def test_staff_reopening_completed_appointment_clears_completion_metadata(patient_token):
    from database import appointments_collection

    appt_id = new_booking(patient_token)
    client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "confirmed"})
    client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "completed"})

    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "confirmed"})
    assert r.status_code == 200, r.text

    stored = client.portal.call(appointments_collection.find_one, {"hospital_id": HID, "appointment_id": appt_id})
    assert stored["status"] == "confirmed"
    assert stored.get("completed_at") is None
    assert stored.get("completed_date") is None
    assert status_of(appt_id) == "confirmed"


def test_patient_cannot_change_status(patient_token):
    appt_id = new_booking(patient_token)
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(patient_token), json={"status": "confirmed"})
    assert r.status_code == 403
    assert status_of(appt_id) == "pending"


def test_anonymous_cannot_change_status(patient_token):
    appt_id = new_booking(patient_token)
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=HDR, json={"status": "confirmed"})
    assert r.status_code in (401, 403)
    assert status_of(appt_id) == "pending"


def test_other_hospital_staff_cannot_change_status(patient_token):
    appt_id = new_booking(patient_token)
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff(OTHER_HID)), json={"status": "confirmed"})
    assert r.status_code == 404
    assert status_of(appt_id) == "pending"


def test_cancel_status_is_not_accepted_through_status_endpoint(patient_token):
    appt_id = new_booking(patient_token)
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "cancelled"})
    assert r.status_code == 422


def test_cancelled_appointment_cannot_be_confirmed(patient_token):
    appt_id = new_booking(patient_token)
    c = client.post(f"/appointments/{appt_id}/cancel", headers=bearer(staff()), json={"reason": "test"})
    assert c.status_code == 200, c.text
    r = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "confirmed"})
    assert r.status_code == 409


def test_complete_persists_to_document_and_survives_refetch(patient_token):
    from database import appointments_collection
    appt_id = new_booking(patient_token)
    c = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "confirmed"})
    assert c.status_code == 200, c.text
    d = client.patch(f"/admin/appointments/{appt_id}/status", headers=bearer(staff()), json={"status": "completed"})
    assert d.status_code == 200, d.text
    stored = client.portal.call(appointments_collection.find_one, {"hospital_id": HID, "appointment_id": appt_id})
    assert stored["status"] == "completed"
    assert "completed_at" in stored and stored["completed_at"] is not None
    assert "completed_date" in stored and stored["completed_date"] == datetime.now(pytz.timezone("Asia/Kolkata")).date().isoformat()
    assert [h["action"] for h in stored["history"]][-1] == "completed"
    assert status_of(appt_id) == "completed"
    listed = client.get("/appointments", headers=bearer(staff())).json()["appointments"]
    assert next(a for a in listed if a["appointment_id"] == appt_id)["status"] == "completed"
    filtered = client.get("/appointments", params={"status": "completed"}, headers=bearer(staff())).json()["appointments"]
    assert appt_id in [a["appointment_id"] for a in filtered]
    not_confirmed = client.get("/appointments", params={"status": "confirmed"}, headers=bearer(staff())).json()["appointments"]
    assert appt_id not in [a["appointment_id"] for a in not_confirmed]


def test_admin_summary_uses_completion_timestamp_not_preferred_date():
    from database import appointments_collection

    hid = "SUMMARYTEST"
    kolkata = pytz.timezone("Asia/Kolkata")
    today = datetime.now(kolkata).date().isoformat()
    yesterday = (datetime.now(kolkata) - timedelta(days=1)).date().isoformat()
    patient = {"full_name": "Summary Patient", "email": "summary.patient@example.com", "phone": "9000000011", "password": "TestPass123"}
    client.portal.call(hospitals_collection.insert_one, {"hospital_id": hid, "name": "Summary Test Hospital"})
    client.portal.call(departments_collection.insert_one,
                       {"hospital_id": hid, "department_id": "summary-dept", "name": "Summary Dept", "consultation_fee": 500, "active": True})
    reg = client.post("/patients/register", headers={"X-Hospital-Id": hid}, json=patient)
    assert reg.status_code == 201, reg.text
    patient_token = reg.json()["access_token"]

    def book_for_date(day):
        r = client.post("/book-appointment", headers={"X-Hospital-Id": hid, **bearer(patient_token)},
                        json={"patient_name": patient["full_name"], "department": "Summary Dept", "preferred_date": day, "preferred_time": "10:30 AM"})
        assert r.status_code == 200, r.text
        return r.json()["appointment_id"]

    appt_today = book_for_date(today)
    client.patch(f"/admin/appointments/{appt_today}/status", headers=bearer(create_access_token("summary-staff", role="staff", hospital_id=hid)), json={"status": "completed"})

    appt_old_date = book_for_date(today)
    client.portal.call(
        appointments_collection.update_one,
        {"hospital_id": hid, "appointment_id": appt_old_date},
        {"$set": {"preferred_date": today, "status": "completed", "completed_at": datetime.now(kolkata) - timedelta(days=1), "completed_date": yesterday}}
    )

    summary = client.get("/admin/summary", headers=bearer(create_access_token("summary-staff", role="staff", hospital_id=hid))).json()
    assert summary["todays_appointments"] >= 1
    assert summary["completed_today"] == 1
    assert summary["completed_appointments"] >= 1
