"""Booking authentication and staff walk-in/recurring booking.
Runs against in-memory MongoDB in its own tenant (AUTHTEST) so it cannot change CITY001 counts in test_e2e.py.
Run from backend/:  python -m pytest -q tests/test_auth_booking.py"""
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

import main
from auth import create_access_token, JWT_SECRET, JWT_ALGORITHM
from database import hospitals_collection, departments_collection

client = TestClient(main.app)
client.__enter__()

HID = "AUTHTEST"
HDR = {"X-Hospital-Id": HID}
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
NO_LOGIN = "Please login to book an appointment"
PATIENT = {"full_name": "Auth Test Patient", "email": "auth.test@example.com", "phone": "9000000001", "password": "TestPass123"}
BOOKING = {"patient_name": "Test Patient", "department": "Cardiology", "preferred_date": TOMORROW, "preferred_time": "10:30 AM"}


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module", autouse=True)
def tenant():
    client.portal.call(hospitals_collection.insert_one, {"hospital_id": HID, "name": "Auth Test Hospital"})
    client.portal.call(departments_collection.insert_one,
                       {"hospital_id": HID, "department_id": "cardiology", "name": "Cardiology", "consultation_fee": 500, "active": True})


@pytest.fixture(scope="module")
def patient(tenant):
    r = client.post("/patients/register", headers=HDR, json=PATIENT)
    assert r.status_code == 201, r.text
    return r.json()


def staff_token():
    return create_access_token("staff-test-user", role="staff", hospital_id=HID)


def test_patient_login_returns_patient_token(patient):
    r = client.post("/patients/login", headers=HDR, json={"identifier": PATIENT["email"], "password": PATIENT["password"]})
    assert r.status_code == 200, r.text
    claims = jwt.decode(r.json()["access_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    assert claims["role"] == "patient"


def test_patient_login_rejects_wrong_password(patient):
    r = client.post("/patients/login", headers=HDR, json={"identifier": PATIENT["email"], "password": "wrong-password"})
    assert r.status_code == 401


def test_patient_token_books_and_appointment_is_listed(patient):
    token = patient["access_token"]
    r = client.post("/book-appointment", headers={**HDR, **bearer(token)}, json=BOOKING)
    assert r.status_code == 200, r.text
    appt_id = r.json()["appointment_id"]
    listed = client.get("/appointments", headers=bearer(token)).json()["appointments"]
    assert appt_id in [a["appointment_id"] for a in listed]
    assert all(a["patient_id"] == patient["patient"]["patient_id"] for a in listed)


def test_staff_token_is_rejected_by_patient_only_booking():
    r = client.post("/book-appointment", headers={**HDR, **bearer(staff_token())}, json=BOOKING)
    assert r.status_code == 401
    assert r.json()["detail"] == NO_LOGIN


def test_missing_token_is_rejected():
    r = client.post("/book-appointment", headers=HDR, json=BOOKING)
    assert r.status_code == 401
    assert r.json()["detail"] == NO_LOGIN


def test_invalid_token_is_rejected():
    r = client.post("/book-appointment", headers={**HDR, **bearer("not.a.real.token")}, json=BOOKING)
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid or expired token"


def test_token_signed_with_other_secret_is_rejected():
    forged = jwt.encode({"sub": "x", "role": "patient", "hid": HID,
                         "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, "other-secret", algorithm=JWT_ALGORITHM)
    r = client.post("/book-appointment", headers={**HDR, **bearer(forged)}, json=BOOKING)
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid or expired token"


def test_expired_patient_token_is_rejected(patient):
    expired = create_access_token(patient["patient"]["patient_id"], role="patient", hospital_id=HID, expires_minutes=-5)
    r = client.post("/book-appointment", headers={**HDR, **bearer(expired)}, json=BOOKING)
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid or expired token"


def test_agent_key_books_without_bearer_token():
    r = client.post("/book-appointment", headers={**HDR, "X-Agent-Key": "agent-secret"}, json=BOOKING)
    assert r.status_code == 200, r.text


def test_wrong_agent_key_is_rejected():
    r = client.post("/book-appointment", headers={**HDR, "X-Agent-Key": "wrong"}, json=BOOKING)
    assert r.status_code == 401
    assert r.json()["detail"] == NO_LOGIN


def test_staff_walk_in_booking_for_existing_patient(patient):
    r = client.post("/book-appointment/walk-in", headers=bearer(staff_token()),
                    json={"patient_id": patient["patient"]["patient_id"], "department": "Cardiology"})
    assert r.status_code == 200, r.text


def test_staff_walk_in_stores_patient_full_name(patient):
    r = client.post("/book-appointment/walk-in", headers=bearer(staff_token()),
                    json={"patient_id": patient["patient"]["patient_id"], "department": "Cardiology"})
    assert r.status_code == 200, r.text
    appt = r.json()["appointment"]
    assert appt["patient_name"] == PATIENT["full_name"]
    assert appt["patient_id"] == patient["patient"]["patient_id"]
    stored = client.get(f"/appointments/{appt['appointment_id']}", headers=bearer(staff_token())).json()["appointment"]
    assert stored["patient_name"] == PATIENT["full_name"]


def test_staff_recurring_booking_stores_patient_full_name(patient):
    r = client.post("/book-appointment/recurring", headers=bearer(staff_token()),
                    json={"patient_id": patient["patient"]["patient_id"], "department": "Cardiology",
                          "first_date": TOMORROW, "appointment_time": "11:00 AM", "frequency": "weekly", "occurrences": 2})
    assert r.status_code == 200, r.text
    appts = r.json()["appointments"]
    assert len(appts) == 2
    assert all(a["patient_name"] == PATIENT["full_name"] for a in appts)


def test_walk_in_for_unknown_patient_is_404(tenant):
    r = client.post("/book-appointment/walk-in", headers=bearer(staff_token()),
                    json={"patient_id": "PAT-DOES-NOT-EXIST", "department": "Cardiology"})
    assert r.status_code == 404


def test_patient_cannot_use_staff_walk_in(patient):
    r = client.post("/book-appointment/walk-in", headers=bearer(patient["access_token"]),
                    json={"patient_id": patient["patient"]["patient_id"], "department": "Cardiology"})
    assert r.status_code == 403


def test_patient_me_endpoint_is_patient_only_so_staff_cannot_use_it_for_dropdown():
    r = client.get("/patients/me", headers=bearer(staff_token()))
    assert r.status_code == 403


def test_staff_can_list_patients_for_booking_dropdown(patient):
    r = client.get("/admin/patients", headers=bearer(staff_token()))
    assert r.status_code == 200, r.text
    ids = [p["patient_id"] for p in r.json()["patients"]]
    assert patient["patient"]["patient_id"] in ids


def test_patient_token_cannot_list_staff_patients(patient):
    r = client.get("/admin/patients", headers=bearer(patient["access_token"]))
    assert r.status_code == 403


def test_staff_book_stores_selected_patient(patient):
    r = client.post("/admin/appointments/book", headers=bearer(staff_token()),
                    json={"patient_id": patient["patient"]["patient_id"], "department": "Cardiology",
                          "preferred_date": TOMORROW, "preferred_time": "2:00 PM"})
    assert r.status_code == 200, r.text
    appt = r.json()["appointment"]
    assert appt["patient_id"] == patient["patient"]["patient_id"]
    assert appt["patient_name"] == PATIENT["full_name"]
    assert appt["source"] == "staff"
    assert appt["preferred_time"] == "2:00 PM"


def test_staff_book_unknown_patient_is_404():
    r = client.post("/admin/appointments/book", headers=bearer(staff_token()),
                    json={"patient_id": "PAT-DOES-NOT-EXIST", "department": "Cardiology", "preferred_date": TOMORROW})
    assert r.status_code == 404


def test_patient_token_cannot_use_staff_book(patient):
    r = client.post("/admin/appointments/book", headers=bearer(patient["access_token"]),
                    json={"patient_id": patient["patient"]["patient_id"], "department": "Cardiology", "preferred_date": TOMORROW})
    assert r.status_code == 403


def test_staff_book_requires_authentication(patient):
    r = client.post("/admin/appointments/book",
                    json={"patient_id": patient["patient"]["patient_id"], "department": "Cardiology", "preferred_date": TOMORROW})
    assert r.status_code in (401, 403)
