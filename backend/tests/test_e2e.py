"""End-to-end API test: in-memory MongoDB, a real local SMTP server, mocked Razorpay HTTP.
Run from backend/:  MONGODB_URI=mongomock:// python -m pytest -q tests"""
import asyncio, hashlib, hmac, json, os, re, time
from datetime import date, timedelta

from aiosmtpd.controller import Controller
from email import message_from_bytes
import pytest
from fastapi.testclient import TestClient

INBOX = []


class Handler:
    async def handle_DATA(self, server, session, envelope):
        m = message_from_bytes(envelope.content)
        text = next((p.get_payload(decode=True).decode() for p in m.walk() if p.get_content_type() == "text/plain"), "")
        INBOX.append({"to": envelope.rcpt_tos[0], "subject": m["Subject"], "text": text})
        return "250 OK"


smtp = Controller(Handler(), hostname="127.0.0.1", port=8025)
smtp.start()

import main  # noqa: E402
from services import payments_gateway as gw  # noqa: E402

client = TestClient(main.app)
client.__enter__()  # run startup (seed)
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
LATER = (date.today() + timedelta(days=3)).isoformat()


def wait_mail(subject_part, to=None, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        for m in INBOX:
            if subject_part in m["subject"] and (to is None or m["to"] == to):
                return m
        time.sleep(0.05)
    raise AssertionError(f"no email with '{subject_part}' to {to}. Inbox: {[x['subject'] for x in INBOX]}")


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


S = {}


def test_01_existing_public_endpoints_still_work():
    assert client.get("/health").json() == {"status": "ok"}
    r = client.post("/faq", json={"question": "What are the visiting hours?"})
    assert r.status_code == 200 and "4:00 PM" in r.json()["answer"]
    assert client.get("/hospital").json()["hospital"]["name"] == "City Hospital"
    docs = client.get("/doctors").json()["doctors"]
    assert len(docs) == 6 and docs[0]["hospital_id"] == "CITY001"
    assert any(d["name"] == "Cardiology" for d in client.get("/departments").json()["departments"])


def test_02_booking_requires_auth_but_agent_still_works():
    body = {"patient_name": "Caller One", "department": "Cardiology", "preferred_date": TOMORROW, "preferred_time": "10:30 AM"}
    assert client.post("/book-appointment", json=body).status_code == 401
    assert client.post("/book-appointment", json=body, headers={"X-Agent-Key": "wrong"}).status_code == 401
    r = client.post("/book-appointment", json=body, headers={"X-Agent-Key": "agent-secret"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["success"] and j["appointment_id"] and j["status"] == "pending"


def test_03_staff_register_locked_and_admin_login():
    r = client.post("/auth/register", json={"username": "admin", "password": "Admin@1234"})
    assert r.status_code == 201 and r.json()["role"] == "admin"
    assert client.post("/auth/register", json={"username": "intruder", "password": "x"}).status_code == 403
    S["admin"] = client.post("/auth/login", json={"username": "admin", "password": "Admin@1234"}).json()["access_token"]
    assert client.post("/auth/register", json={"username": "nurse", "password": "Nurse@1234"}, headers=H(S["admin"])).json()["role"] == "staff"


def test_04_patient_register_login_welcome_email():
    r = client.post("/patients/register", json={"full_name": "Priya Nair", "email": "Priya@Example.com", "phone": "98765 00001", "password": "secret123"})
    assert r.status_code == 201, r.text
    S["p1"] = r.json()["access_token"]
    assert r.json()["patient"].get("password_hash") is None
    wait_mail("Welcome to MediAssist", "priya@example.com")
    assert client.post("/patients/register", json={"full_name": "Dup", "email": "priya@example.com", "phone": "9876500002", "password": "secret123"}).status_code == 409
    assert client.post("/patients/login", json={"identifier": "9876500001", "password": "secret123"}).status_code == 200
    assert client.post("/patients/login", json={"identifier": "priya@example.com", "password": "nope"}).status_code == 401
    S["p2"] = client.post("/patients/register", json={"full_name": "Rohit Kumar", "email": "rohit@example.com", "phone": "9876500003", "password": "secret123"}).json()["access_token"]


def test_05_patient_cannot_reach_admin():
    for path in ("/admin/summary", "/escalations", "/dashboard/summary", "/admin/patients", "/admin/conversations", "/auth/me"):
        assert client.get(path, headers=H(S["p1"])).status_code == 403, path
    assert client.patch("/admin/appointments/X/status", json={"status": "confirmed"}, headers=H(S["p1"])).status_code == 403
    assert client.get("/admin/summary").status_code in (401, 403)


def test_06_patient_booking_creates_invoice_notification_email_and_ws():
    with client.websocket_connect(f"/ws?token={S['admin']}") as ws:
        r = client.post("/book-appointment", headers=H(S["p1"]), json={"patient_name": "Priya Nair", "department": "Cardiology",
                                                                     "preferred_date": TOMORROW, "preferred_time": "10:30 AM", "doctor_id": "rahul-sharma"})
        assert r.status_code == 200, r.text
        evt = json.loads(ws.receive_text())
    j = r.json()
    S["a1"], S["inv1"] = j["appointment_id"], j["invoice_id"]
    assert evt["event"] == "notification" and evt["notification"]["type"] == "new_appointment"
    assert "Priya Nair booked a Cardiology appointment" in evt["notification"]["message"]
    mail = wait_mail("Appointment Booking Confirmation", "priya@example.com")
    assert S["a1"] in mail["text"] and "Dr. Rahul Sharma" in mail["text"] and "10:30 AM" in mail["text"]
    # double booking the same doctor/slot is refused
    r2 = client.post("/book-appointment", headers=H(S["p2"]), json={"patient_name": "Rohit", "department": "Cardiology",
                                                                      "preferred_date": TOMORROW, "preferred_time": "10:30 AM", "doctor_id": "rahul-sharma"})
    assert r2.status_code == 409
    assert client.post("/book-appointment", headers=H(S["p1"]), json={"patient_name": "x", "department": "Cardiology", "preferred_date": "2000-01-01", "preferred_time": "9:00 AM"}).status_code == 422


def test_07_scoping_patient_sees_own_admin_sees_all():
    mine = client.get("/appointments", headers=H(S["p1"])).json()["appointments"]
    assert [a["appointment_id"] for a in mine] == [S["a1"]]
    assert client.get("/appointments", headers=H(S["p2"])).json()["appointments"] == []
    assert client.get(f"/appointments/{S['a1']}", headers=H(S["p2"])).status_code == 404
    allx = client.get("/appointments", headers=H(S["admin"])).json()["appointments"]
    assert len(allx) == 2
    inv = client.get(f"/invoices/{S['inv1']}", headers=H(S["p1"])).json()
    assert inv["invoice"]["total"] == 1000 and inv["invoice"]["status"] == "pending"
    assert client.get(f"/invoices/{S['inv1']}", headers=H(S["p2"])).status_code == 404


def test_08_admin_confirm_reschedule_cancel_emails():
    r = client.patch(f"/admin/appointments/{S['a1']}/status", json={"status": "confirmed"}, headers=H(S["admin"]))
    assert r.json()["appointment"]["status"] == "confirmed"
    m = wait_mail("Appointment Confirmed", "priya@example.com")
    assert "123 Health Street" in m["text"]
    before = len(INBOX)
    client.patch(f"/admin/appointments/{S['a1']}/status", json={"status": "confirmed"}, headers=H(S["admin"]))
    time.sleep(0.3)
    assert len(INBOX) == before  # no duplicate email for an unchanged status
    r = client.post(f"/appointments/{S['a1']}/reschedule", json={"preferred_date": LATER, "preferred_time": "11:00 AM"}, headers=H(S["p1"]))
    assert r.json()["appointment"]["status"] == "rescheduled"
    m = wait_mail("Appointment Rescheduled", "priya@example.com")
    assert "Previous" in m["text"] and "11:00 AM" in m["text"]
    admin_n = client.get("/notifications", headers=H(S["admin"])).json()["notifications"]
    assert any(n["type"] == "appointment_rescheduled_by_patient" for n in admin_n)
    r = client.post(f"/appointments/{S['a1']}/cancel", json={"reason": "Doctor unavailable"}, headers=H(S["admin"]))
    assert r.json()["appointment"]["status"] == "cancelled"
    m = wait_mail("Appointment Cancelled by City Hospital", "priya@example.com")
    assert client.get(f"/invoices/{S['inv1']}", headers=H(S["p1"])).json()["invoice"]["status"] == "cancelled"


def test_09_cash_payment_and_refund():
    r = client.post("/book-appointment", headers=H(S["p1"]), json={"patient_name": "Priya Nair", "department": "Dermatology", "preferred_date": TOMORROW, "preferred_time": "2:00 PM"})
    S["inv2"] = r.json()["invoice_id"]
    # raw card data is rejected outright
    bad = client.post("/payments/order", headers=H(S["p1"]), json={"invoice_id": S["inv2"], "method": "card", "card_number": "4111111111111111", "cvv": "123"})
    assert bad.status_code == 422
    # online without gateway keys → honest 503, nothing marked paid
    assert client.post("/payments/order", headers=H(S["p1"]), json={"invoice_id": S["inv2"], "method": "upi", "upi_app": "gpay"}).status_code == 503
    r = client.post("/payments/order", headers=H(S["p1"]), json={"invoice_id": S["inv2"], "method": "cash"})
    pay = r.json()["payment"]
    assert r.json()["mode"] == "cash" and pay["status"] == "pending"
    assert client.get(f"/invoices/{S['inv2']}", headers=H(S["p1"])).json()["invoice"]["status"] == "pending"
    assert client.post(f"/admin/payments/{pay['payment_id']}/mark-paid", headers=H(S["p1"])).status_code == 403
    r = client.post(f"/admin/payments/{pay['payment_id']}/mark-paid", headers=H(S["admin"]))
    assert r.json()["payment"]["status"] == "paid" and r.json()["payment"]["transaction_id"].startswith("CASH-")
    m = wait_mail("Payment Confirmation", "priya@example.com")
    assert S["inv2"] in m["text"] and "Cash at Hospital" in m["text"]
    assert client.get("/admin/summary", headers=H(S["admin"])).json()["revenue"] == 600
    r = client.post(f"/admin/payments/{pay['payment_id']}/refund", json={}, headers=H(S["admin"]))
    assert r.json()["payment"]["status"] == "refunded"
    wait_mail("Payment Refund", "priya@example.com")


def test_10_razorpay_flow_verified_with_gateway():
    os.environ.update({"RAZORPAY_KEY_ID": "rzp_test_x", "RAZORPAY_KEY_SECRET": "sek", "RAZORPAY_WEBHOOK_SECRET": "whs"})
    state = {}

    async def create_order(amount, receipt, notes):
        state["order"] = {"id": "order_T1", "amount": int(amount * 100), "currency": "INR"}
        return state["order"]

    async def fetch_payment(pid):
        return {"id": pid, "order_id": "order_T1", "status": state.get("status", "captured"), "method": "upi"}

    gw.create_order, gw.fetch_payment = create_order, fetch_payment
    r = client.post("/book-appointment", headers=H(S["p2"]), json={"patient_name": "Rohit Kumar", "department": "Orthopedics", "preferred_date": TOMORROW, "preferred_time": "3:00 PM"})
    inv = r.json()["invoice_id"]
    o = client.post("/payments/order", headers=H(S["p2"]), json={"invoice_id": inv, "method": "upi", "upi_app": "phonepe"}).json()
    assert o["mode"] == "razorpay" and o["key_id"] == "rzp_test_x" and "sek" not in json.dumps(o)
    # forged signature → rejected, invoice stays unpaid
    assert client.post("/payments/verify", headers=H(S["p2"]), json={"razorpay_order_id": "order_T1", "razorpay_payment_id": "pay_1", "razorpay_signature": "forged"}).status_code == 400
    assert client.get(f"/invoices/{inv}", headers=H(S["p2"])).json()["invoice"]["status"] == "pending"
    sig = hmac.new(b"sek", b"order_T1|pay_1", hashlib.sha256).hexdigest()
    r = client.post("/payments/verify", headers=H(S["p2"]), json={"razorpay_order_id": "order_T1", "razorpay_payment_id": "pay_1", "razorpay_signature": sig})
    assert r.json()["payment"]["status"] == "paid" and r.json()["payment"]["transaction_id"] == "pay_1"
    wait_mail("Payment Confirmation", "rohit@example.com")
    # webhook replay of the same capture is idempotent (no second email)
    body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_1", "order_id": "order_T1", "method": "upi"}}}}).encode()
    before = len([m for m in INBOX if "Payment Confirmation" in m["subject"]])
    assert client.post("/payments/webhook/razorpay", content=body, headers={"X-Razorpay-Signature": "bad"}).status_code == 400
    ok = client.post("/payments/webhook/razorpay", content=body, headers={"X-Razorpay-Signature": hmac.new(b"whs", body, hashlib.sha256).hexdigest()})
    assert ok.status_code == 200
    time.sleep(0.3)
    assert len([m for m in INBOX if "Payment Confirmation" in m["subject"]]) == before
    # a failed payment via webhook → failed email, invoice not paid
    r = client.post("/book-appointment", headers=H(S["p2"]), json={"patient_name": "Rohit Kumar", "department": "Neurology", "preferred_date": TOMORROW, "preferred_time": "4:00 PM"})
    inv3 = r.json()["invoice_id"]

    async def create_order2(amount, receipt, notes):
        return {"id": "order_T2", "amount": int(amount * 100), "currency": "INR"}
    gw.create_order = create_order2
    client.post("/payments/order", headers=H(S["p2"]), json={"invoice_id": inv3, "method": "card"})
    body = json.dumps({"event": "payment.failed", "payload": {"payment": {"entity": {"id": "pay_2", "order_id": "order_T2", "error_description": "Card declined"}}}}).encode()
    client.post("/payments/webhook/razorpay", content=body, headers={"X-Razorpay-Signature": hmac.new(b"whs", body, hashlib.sha256).hexdigest()})
    m = wait_mail("Payment Failed", "rohit@example.com")
    assert client.get(f"/invoices/{inv3}", headers=H(S["p2"])).json()["invoice"]["status"] == "pending"
    for k in ("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"):
        os.environ.pop(k)


def test_11_notification_center():
    j = client.get("/notifications", headers=H(S["p1"])).json()
    types = {n["type"] for n in j["notifications"]}
    assert {"appointment_booked", "appointment_confirmed", "appointment_rescheduled", "appointment_cancelled", "payment_success", "payment_refunded"} <= types
    assert all(n["patient_id"] for n in j["notifications"])
    assert j["unread"] > 0
    client.post("/notifications/read-all", headers=H(S["p1"]))
    assert client.get("/notifications/unread-count", headers=H(S["p1"])).json()["unread"] == 0
    # p2 never sees p1's notifications
    assert all(n["type"] != "appointment_confirmed" for n in client.get("/notifications", headers=H(S["p2"])).json()["notifications"])


def test_12_conversations_from_bolna_and_escalation():
    assert client.post("/agent/bolna/webhook", json={"id": "exec-1"}).status_code == 401
    r = client.post("/agent/bolna/webhook?key=agent-secret", json={"id": "exec-1", "status": "in-progress",
          "transcript": "assistant: Hello, City Hospital.\nuser: I need a cardiologist.", "telephony_data": {"from_number": "+919800000000"}})
    assert r.status_code == 200
    live = client.get("/admin/conversations?state=live", headers=H(S["admin"])).json()
    assert live["counts"]["live"] == 1 and live["conversations"][0]["message_count"] == 2
    client.post("/escalate", json={"patient_name": "Caller", "reason": "Wants billing staff"}, headers={"X-Conversation-Id": "exec-1"})
    c = client.get("/admin/conversations", headers=H(S["admin"])).json()["conversations"][0]
    assert c["status"] == "escalated"
    assert any(n["type"] == "new_escalation" for n in client.get("/notifications", headers=H(S["admin"])).json()["notifications"])
    assert client.get("/escalations", headers=H(S["admin"])).json()["escalations"][0]["hospital_id"] == "CITY001"


def test_13_forgot_and_reset_password():
    assert client.post("/patients/forgot-password", json={"email": "nobody@example.com"}).json()["success"]
    client.post("/patients/forgot-password", json={"email": "priya@example.com"})
    m = wait_mail("Reset your MediAssist password", "priya@example.com")
    token = re.search(r"token=([\w\-]+)", m["text"]).group(1)
    assert client.post("/patients/reset-password", json={"token": token, "password": "newsecret1"}).status_code == 200
    assert client.post("/patients/reset-password", json={"token": token, "password": "again1234"}).status_code == 400
    assert client.post("/patients/login", json={"identifier": "priya@example.com", "password": "newsecret1"}).status_code == 200


def test_14_tenant_isolation():
    from database import hospitals_collection
    asyncio.get_event_loop  # noqa
    client.portal.call(hospitals_collection.insert_one, {"hospital_id": "SUN002", "name": "Sunrise Medical Center"})
    r = client.post("/patients/register", headers={"X-Hospital-Id": "SUN002"}, json={"full_name": "Other", "email": "o@example.com", "phone": "9876500009", "password": "secret123"})
    tok = r.json()["access_token"]
    client.portal.call(__import__("database").departments_collection.insert_one, {"hospital_id": "SUN002", "department_id": "general", "name": "General", "consultation_fee": 300, "active": True})
    r = client.post("/book-appointment", headers=H(tok), json={"patient_name": "Other", "department": "General", "preferred_date": TOMORROW, "preferred_time": "9:00 AM"})
    assert r.status_code == 200, r.text
    ids = [a["appointment_id"] for a in client.get("/appointments", headers=H(S["admin"])).json()["appointments"]]
    assert r.json()["appointment_id"] not in ids  # City Hospital admin never sees Sunrise data
    assert all(n["hospital_id"] == "CITY001" for n in client.get("/notifications", headers=H(S["admin"])).json()["notifications"])
    r = client.post("/patients/register", headers={"X-Hospital-Id": "NOPE9"}, json={"full_name": "Xavier", "email": "x@example.com", "phone": "9876500010", "password": "secret123"}); assert r.status_code == 404, r.text


def test_15_admin_views_and_email_logs():
    s = client.get("/admin/summary", headers=H(S["admin"])).json()
    assert s["total_patients"] == 2 and s["email_configured"] is True
    assert len(client.get("/admin/patients", headers=H(S["admin"])).json()["patients"]) == 2
    a = client.get("/admin/analytics?days=7", headers=H(S["admin"])).json()
    assert len(a["series"]) == 7 and sum(x["appointments"] for x in a["series"]) >= 4
    logs = client.get("/admin/email-logs", headers=H(S["admin"])).json()["emails"]
    assert logs and all(e["status"] == "sent" for e in logs)
    assert client.get("/dashboard/summary", headers=H(S["admin"])).status_code == 200


def test_16_contact_form_reaches_admin():
    assert client.post("/contact", json={"name": "A", "email": "a@b.co", "message": "short"}).status_code == 422
    r = client.post("/contact", json={"name": "Meera", "email": "meera@example.com", "message": "Do you offer weekend physiotherapy?"})
    assert r.status_code == 201
    assert any(n["type"] == "contact_message" for n in client.get("/notifications", headers=H(S["admin"])).json()["notifications"])
