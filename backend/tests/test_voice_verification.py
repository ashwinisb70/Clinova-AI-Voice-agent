"""Voice verification for staff-booked appointments and cross-hospital isolation (in-memory MongoDB).
Run from backend/:  python -m pytest -q tests/test_voice_verification.py"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import main
from auth import create_access_token
from database import departments_collection, hospitals_collection

client = TestClient(main.app)
client.__enter__()

HID = "VERIFYTEST"
OTHER = "VERIFYOTHER"
PHONE = "9000000005"
OTHER_PHONE = "9000000006"
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()
NOT_FOUND = "We could not find an appointment matching those details. Please check the reference number and the phone number on your account."


def agent(hid):
    return {"X-Agent-Key": "agent-secret", "X-Hospital-Id": hid}


def staff(hid):
    return {"Authorization": "Bearer " + create_access_token("verify-staff", role="staff", hospital_id=hid)}


def register(hid, name, phone):
    r = client.post("/patients/register", headers={"X-Hospital-Id": hid},
                    json={"full_name": name, "email": f"{phone}@example.com", "phone": phone, "password": "TestPass123"})
    assert r.status_code == 201, r.text
    return r.json()["patient"]["patient_id"]


@pytest.fixture(scope="module", autouse=True)
def tenants():
    for hid, name in ((HID, "Verify Hospital"), (OTHER, "Other Hospital")):
        client.portal.call(hospitals_collection.insert_one, {"hospital_id": hid, "name": name})
        client.portal.call(departments_collection.insert_one, {"hospital_id": hid, "department_id": "cardiology",
                                                              "name": "Cardiology", "consultation_fee": 500, "active": True})


@pytest.fixture(scope="module")
def patient_id():
    return register(HID, "Staff Booked Patient", PHONE)


@pytest.fixture(scope="module")
def staff_booked(patient_id):
    r = client.post("/admin/appointments/book", headers=staff(HID),
                    json={"patient_id": patient_id, "department": "Cardiology", "preferred_date": TOMORROW, "preferred_time": "9:00 AM"})
    assert r.status_code == 200, r.text
    return r.json()["appointment"]["appointment_id"]


def test_staff_booked_appointment_status_with_registered_phone(staff_booked):
    r = client.post("/agent/appointments/status", headers=agent(HID), json={"appointment_id": staff_booked, "phone": PHONE})
    assert r.status_code == 200, r.text
    assert r.json()["appointment"]["status"] == "pending"


def test_staff_booked_appointment_wrong_phone_is_rejected(staff_booked):
    r = client.post("/agent/appointments/status", headers=agent(HID), json={"appointment_id": staff_booked, "phone": "9111111111"})
    assert r.status_code == 404
    assert r.json()["detail"] == NOT_FOUND


def test_staff_booked_appointment_can_be_rescheduled_by_voice(staff_booked):
    r = client.post("/agent/appointments/reschedule", headers=agent(HID),
                    json={"appointment_id": staff_booked, "phone": PHONE, "preferred_date": NEXT_WEEK, "preferred_time": "10:00 AM"})
    assert r.status_code == 200, r.text
    assert r.json()["appointment"]["preferred_date"] == NEXT_WEEK


def test_other_hospital_reference_is_not_visible(staff_booked):
    r = client.post("/agent/appointments/status", headers=agent(OTHER), json={"appointment_id": staff_booked, "phone": PHONE})
    assert r.status_code == 404
    assert r.json()["detail"] == NOT_FOUND


def test_same_phone_in_other_hospital_cannot_verify_appointment(staff_booked):
    register(OTHER, "Other Hospital Patient", OTHER_PHONE)
    r = client.post("/agent/appointments/status", headers=agent(OTHER), json={"appointment_id": staff_booked, "phone": OTHER_PHONE})
    assert r.status_code == 404
    assert r.json()["detail"] == NOT_FOUND


def test_unknown_reference_message_does_not_reveal_existence():
    r = client.post("/agent/appointments/status", headers=agent(HID), json={"appointment_id": "ZZZZZZZZ", "phone": PHONE})
    assert r.status_code == 404
    assert r.json()["detail"] == NOT_FOUND


def test_voice_endpoints_are_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]
    for path in ("/agent/appointments/status", "/agent/appointments/reschedule", "/agent/appointments/cancel"):
        assert path in paths
        assert "post" in paths[path]


@pytest.mark.parametrize("bad_time", ["", "   ", "\t"])
def test_reschedule_rejects_empty_or_whitespace_time(staff_booked, bad_time):
    r = client.post("/agent/appointments/reschedule", headers=agent(HID),
                    json={"appointment_id": staff_booked, "phone": PHONE, "preferred_date": NEXT_WEEK, "preferred_time": bad_time})
    assert r.status_code == 422
    assert "new appointment time" in str(r.json()["detail"])


def test_reschedule_empty_time_changes_nothing(staff_booked):
    before = client.post("/agent/appointments/status", headers=agent(HID), json={"appointment_id": staff_booked, "phone": PHONE}).json()
    client.post("/agent/appointments/reschedule", headers=agent(HID),
                json={"appointment_id": staff_booked, "phone": PHONE, "preferred_date": NEXT_WEEK, "preferred_time": ""})
    after = client.post("/agent/appointments/status", headers=agent(HID), json={"appointment_id": staff_booked, "phone": PHONE}).json()
    assert before["appointment"] == after["appointment"]


def test_malformed_booking_body_returns_422_not_server_error():
    r = client.post("/book-appointment", headers=agent(HID), json={"department": "Cardiology", "preferred_date": TOMORROW})
    assert r.status_code == 422


def test_form_encoded_booking_body_returns_422_not_server_error():
    r = client.post("/book-appointment", headers={**agent(HID), "Content-Type": "application/x-www-form-urlencoded"},
                    data={"patient_name": "Form Caller", "department": "Cardiology", "preferred_date": TOMORROW})
    assert r.status_code == 422
