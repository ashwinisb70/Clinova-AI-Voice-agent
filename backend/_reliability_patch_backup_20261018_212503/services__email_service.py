"""Transactional email via SMTP. Configure with environment variables (never in React):

EMAIL_HOST, EMAIL_PORT (587), EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM,
EMAIL_USE_TLS (true = STARTTLS), EMAIL_USE_SSL (true = implicit TLS, usually port 465)

Every email is written to `email_logs` first (status pending → sent / failed), and sending
happens in the background so a mail-server problem never fails a booking or payment.
Swap `_send_smtp` for a provider API (SendGrid, SES, Resend…) without touching callers.
"""
import asyncio
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from database import email_logs_collection
from services.common import now, short_id

log = logging.getLogger("mediassist.email")

_background = set()


def email_configured() -> bool:
    return bool(os.getenv("EMAIL_HOST") and os.getenv("EMAIL_FROM"))


def _send_smtp(to: str, subject: str, html: str, text: str, from_name: str):
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", "587"))
    user = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")
    sender = os.getenv("EMAIL_FROM")
    use_ssl = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
    use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    timeout = float(os.getenv("EMAIL_TIMEOUT_SECONDS", "45"))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, sender))
    msg["To"] = to
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=timeout) as s:
            if user:
                s.login(user, password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=timeout) as s:
            if use_tls:
                s.starttls(context=ssl.create_default_context())
            if user:
                s.login(user, password)
            s.send_message(msg)


async def _deliver(email_id: str):
    doc = await email_logs_collection.find_one({"email_id": email_id})
    if not doc:
        return
    if not email_configured():
        await email_logs_collection.update_one({"email_id": email_id}, {"$set": {
            "status": "failed", "error": "Email service is not configured (EMAIL_HOST / EMAIL_FROM)", "updated_at": now()}})
        log.warning("Email %s not sent: email service not configured", email_id)
        return
    try:
        await asyncio.to_thread(_send_smtp, doc["to"], doc["subject"], doc["html"], doc["text"], doc.get("from_name", "MediAssist"))
        await email_logs_collection.update_one({"email_id": email_id}, {"$set": {"status": "sent", "sent_at": now(), "error": None, "updated_at": now()},
                                                                         "$inc": {"attempts": 1}})
    except Exception as exc:  # noqa: BLE001 — any SMTP failure is logged, never raised
        log.exception("Email %s failed", email_id)
        await email_logs_collection.update_one({"email_id": email_id}, {"$set": {"status": "failed", "error": str(exc)[:500], "updated_at": now()},
                                                                         "$inc": {"attempts": 1}})


async def queue_email(*, to: str, subject: str, html: str, text: str, kind: str, hospital_id: str,
                      patient_id: str = None, ref: dict = None, from_name: str = "MediAssist") -> str:
    if email_logs_collection is None or not to:
        return None
    email_id = short_id("EML-")
    await email_logs_collection.insert_one({
        "email_id": email_id, "hospital_id": hospital_id, "patient_id": patient_id, "to": to,
        "subject": subject, "html": html, "text": text, "kind": kind, "ref": ref or {},
        "from_name": from_name, "status": "pending", "attempts": 0, "error": None,
        "created_at": now(), "updated_at": now(),
    })
    task = asyncio.create_task(_deliver(email_id))
    _background.add(task)
    task.add_done_callback(_background.discard)
    return email_id


async def retry_email(email_id: str):
    await email_logs_collection.update_one({"email_id": email_id}, {"$set": {"status": "pending", "updated_at": now()}})
    await _deliver(email_id)
    return await email_logs_collection.find_one({"email_id": email_id})
