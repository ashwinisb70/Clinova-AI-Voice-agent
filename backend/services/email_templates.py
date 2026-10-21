"""Branded, mobile-friendly email templates. Every value comes from the database record passed in."""
import html as _html
import os

from services.common import pretty_date

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

STATUS_COLORS = {
    "pending": ("#B46E0A", "#FEF4E0"), "confirmed": ("#1567D3", "#E8F1FD"), "completed": ("#0F9686", "#E2F7F3"),
    "cancelled": ("#D5343E", "#FDECED"), "rescheduled": ("#6D4AE0", "#EFEAFD"), "paid": ("#0F9686", "#E2F7F3"),
    "failed": ("#D5343E", "#FDECED"), "refunded": ("#5B6B82", "#EEF2F7"),
}


def e(v):
    return _html.escape(str(v if v not in (None, "") else "—"))


def _rows(rows):
    return "".join(
        f'<tr><td style="padding:8px 0;color:#5B6B82;font-size:14px;width:44%;vertical-align:top">{e(k)}</td>'
        f'<td style="padding:8px 0;color:#0B2447;font-size:14px;font-weight:600">{e(v)}</td></tr>' for k, v in rows)


def _badge(status):
    fg, bg = STATUS_COLORS.get(str(status).lower(), ("#1567D3", "#E8F1FD"))
    return (f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;background:{bg};color:{fg};'
            f'font-size:12px;font-weight:700;letter-spacing:.3px">{e(str(status).upper())}</span>')


def layout(hospital: dict, heading: str, intro: str, rows, status=None, cta=None, note=None) -> str:
    h = hospital or {}
    cta_html = (f'<p style="margin:28px 0 8px"><a href="{e(cta[1])}" style="background:#1567D3;color:#fff;text-decoration:none;'
                f'padding:12px 22px;border-radius:8px;font-weight:600;font-size:14px;display:inline-block">{e(cta[0])}</a></p>') if cta else ""
    return f"""<!doctype html><html><body style="margin:0;background:#F3F8FE;font-family:Segoe UI,Arial,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F8FE;padding:24px 12px"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#fff;border:1px solid #DCE7F5;border-radius:16px;overflow:hidden">
<tr><td style="background:#1567D3;padding:20px 28px;color:#fff">
<div style="font-size:20px;font-weight:800">MediAssist</div><div style="font-size:13px;opacity:.85">{e(h.get('name','City Hospital'))}</div></td></tr>
<tr><td style="padding:28px">
<h1 style="margin:0 0 6px;font-size:20px;color:#0B2447">{e(heading)}</h1>
{('<p style="margin:10px 0 0">' + _badge(status) + '</p>') if status else ''}
<p style="margin:16px 0 8px;color:#33445C;font-size:15px;line-height:1.6">{intro}</p>
<table role="presentation" width="100%" style="border-top:1px solid #E8EEF7;margin-top:12px">{_rows(rows)}</table>
{f'<p style="margin:16px 0 0;color:#5B6B82;font-size:13px;line-height:1.6">{note}</p>' if note else ''}
{cta_html}
</td></tr>
<tr><td style="background:#F8FAFE;border-top:1px solid #E8EEF7;padding:18px 28px;color:#5B6B82;font-size:12px;line-height:1.7">
<strong style="color:#0B2447">{e(h.get('name','City Hospital'))}</strong><br>{e(h.get('address',''))}<br>
{e(h.get('phone',''))} · {e(h.get('email',''))}<br>Emergency: {e(h.get('emergency_phone','112'))} (24/7)
<br><br>This is an automated message from MediAssist. MediAssist is an AI assistant, not a doctor.</td></tr>
</table></td></tr></table></body></html>"""


def _text(heading, intro_plain, rows, hospital):
    body = "\n".join(f"{k}: {v if v not in (None, '') else '—'}" for k, v in rows)
    return f"{heading}\n\n{intro_plain}\n\n{body}\n\n— MediAssist, {hospital.get('name', 'City Hospital')}\n{hospital.get('phone', '')} | {hospital.get('email', '')}"


def appointment_rows(a):
    return [("Appointment ID", a.get("appointment_id")), ("Department", a.get("department")),
            ("Doctor", a.get("doctor_name") or "Assigned by the hospital"), ("Date", pretty_date(a.get("preferred_date"))),
            ("Time", a.get("preferred_time")), ("Status", str(a.get("status", "")).capitalize())]


def render(kind: str, *, hospital: dict, patient: dict, appointment: dict = None, previous: dict = None,
           invoice: dict = None, payment: dict = None, extra: dict = None):
    """Returns (subject, html, text)."""
    hn = hospital.get("name", "City Hospital")
    name = patient.get("full_name") or patient.get("patient_name") or "there"
    hello = f"Hello {e(name)},"
    a = appointment or {}
    extra = extra or {}
    link_appts = f"{FRONTEND_URL}/account/appointments"

    if kind == "registration":
        subject = f"Welcome to MediAssist — {hn}"
        heading = "Your account is ready"
        intro = f"{hello}<br>Your MediAssist patient account at {e(hn)} has been created. You can now book appointments, view bills and pay online."
        rows = [("Name", name), ("Email", patient.get("email")), ("Phone", patient.get("phone"))]
        cta, status, note = ("Book an appointment", f"{FRONTEND_URL}/appointments/book"), None, None
    elif kind == "appointment_booked":
        subject = f"Appointment Booking Confirmation — MediAssist {hn}"
        heading = "Appointment request received"
        intro = f"{hello}<br>Your appointment request has been successfully received and is awaiting confirmation from {e(hn)}."
        rows, status, cta = appointment_rows(a), a.get("status"), ("View my appointments", link_appts)
        note = f"{e(hn)} will confirm your appointment shortly."
    elif kind == "appointment_pending":
        subject = "Appointment Request Pending"
        heading = "Your appointment is awaiting confirmation"
        intro = f"{hello}<br>Your appointment request has been received and is currently awaiting hospital confirmation."
        rows, status, cta, note = appointment_rows(a), "pending", ("View my appointments", link_appts), None
    elif kind == "appointment_confirmed":
        subject = f"Appointment Confirmed — MediAssist {hn}"
        heading = "Your appointment has been confirmed"
        intro = f"{hello}<br>Your appointment has been confirmed. Please arrive 15 minutes early and bring a photo ID."
        rows = appointment_rows(a) + [("Hospital address", hospital.get("address"))]
        status, cta, note = "confirmed", ("View my appointments", link_appts), None
    elif kind == "appointment_completed":
        subject = f"Thank you for visiting — MediAssist {hn}"
        heading = "Your appointment is complete"
        intro = f"{hello}<br>Thank you for visiting {e(hn)}. Your bill is available in your MediAssist account."
        rows, status, cta, note = appointment_rows(a), "completed", ("View billing", f"{FRONTEND_URL}/account/billing"), None
    elif kind in ("appointment_cancelled", "appointment_cancelled_by_hospital"):
        by_hospital = kind.endswith("by_hospital")
        subject = f"Appointment Cancelled by {hn}" if by_hospital else f"Appointment Cancelled — MediAssist {hn}"
        heading = "Appointment cancelled"
        intro = (f"{hello}<br>Your appointment scheduled for {e(pretty_date(a.get('preferred_date')))} at {e(a.get('preferred_time'))}"
                 f" with {e(a.get('doctor_name') or a.get('department'))} has been cancelled by {e(hn)}. Please login to MediAssist to book another appointment."
                 if by_hospital else f"{hello}<br>Your appointment has been cancelled successfully.")
        rows = appointment_rows(a) + ([("Reason", extra.get("reason"))] if extra.get("reason") else [])
        status, cta, note = "cancelled", ("Book another appointment", f"{FRONTEND_URL}/appointments/book"), None
    elif kind in ("appointment_rescheduled", "appointment_rescheduled_by_hospital"):
        subject = f"Appointment Rescheduled — MediAssist {hn}"
        heading = "Your appointment has been rescheduled"
        who = e(hn) if kind.endswith("by_hospital") else "you"
        intro = f"{hello}<br>Your appointment has been rescheduled by {who}."
        p = previous or {}
        rows = [("Appointment ID", a.get("appointment_id")),
                ("Previous", f"{pretty_date(p.get('preferred_date'))} — {p.get('preferred_time')}"),
                ("New", f"{pretty_date(a.get('preferred_date'))} — {a.get('preferred_time')}"),
                ("Doctor", a.get("doctor_name") or "Assigned by the hospital"), ("Department", a.get("department")),
                ("Status", str(a.get("status", "")).capitalize())]
        status, cta, note = a.get("status"), ("View my appointments", link_appts), None
    elif kind in ("payment_success", "payment_failed", "payment_refunded"):
        inv, pay = invoice or {}, payment or {}
        rows = [("Patient", name), ("Invoice", inv.get("invoice_id")), ("Appointment", inv.get("appointment_id")),
                ("Amount", f"₹{inv.get('total', pay.get('amount', 0)):,.2f}"), ("Payment method", pay.get("method_label") or pay.get("method")),
                ("Transaction ID", pay.get("transaction_id") or pay.get("gateway_payment_id")),
                ("Date", (pay.get("paid_at") or pay.get("updated_at") or "").strftime("%d %B %Y, %I:%M %p") if hasattr(pay.get("paid_at") or pay.get("updated_at"), "strftime") else "")]
        if kind == "payment_success":
            subject, heading, status = f"Payment Confirmation — MediAssist {hn}", "Payment successful", "paid"
            intro, note, cta = f"{hello}<br>We have received your payment. Thank you.", None, ("View billing", f"{FRONTEND_URL}/account/billing")
        elif kind == "payment_failed":
            subject, heading, status = f"Payment Failed — MediAssist {hn}", "Payment failed", "failed"
            intro = f"{hello}<br>Your payment could not be completed. No amount has been marked as paid on your invoice."
            note, cta = extra.get("reason"), ("Retry payment", f"{FRONTEND_URL}/account/billing/{inv.get('invoice_id')}")
        else:
            subject, heading, status = f"Payment Refund — MediAssist {hn}", "Payment refunded", "refunded"
            intro = f"{hello}<br>A refund has been issued for your payment."
            rows = rows[:3] + [("Original amount", f"₹{pay.get('amount', 0):,.2f}"), ("Refund amount", f"₹{pay.get('refund_amount', pay.get('amount', 0)):,.2f}"),
                               ("Transaction ID", pay.get("transaction_id")), ("Refund ID", pay.get("refund_id")), ("Refund status", "Refunded"),
                               ("Refund date", pay.get("refunded_at").strftime("%d %B %Y") if hasattr(pay.get("refunded_at"), "strftime") else "")]
            note, cta = "Refunds usually reach your account within 5–7 working days, depending on your bank.", None
    elif kind == "password_reset":
        subject = f"Reset your MediAssist password — {hn}"
        heading = "Reset your password"
        intro = f"{hello}<br>We received a request to reset your password. This link expires in 30 minutes. If you didn't ask for this, you can ignore this email."
        rows, status, note = [], None, None
        cta = ("Reset password", extra["reset_url"])
    else:
        raise ValueError(f"Unknown email kind: {kind}")

    intro_plain = _html.unescape(intro.replace("<br>", "\n"))
    text = _text(heading, intro_plain, rows, hospital) + (f"\n\n{cta[0]}: {cta[1]}" if cta else "")
    return subject, layout(hospital, heading, intro, rows, status, cta, note), text
