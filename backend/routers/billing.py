"""Invoices and payments. Online payments go through Razorpay; an invoice is only marked
PAID after the gateway confirms the payment (API check and/or signed webhook)."""
import json
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from auth import get_current_user, require_patient, require_staff, STAFF_ROLES
from database import invoices_collection, payments_collection, appointments_collection, patients_collection, require_db
from services import payments_gateway as gw
from services.common import now, short_id, serialize, scoped
from services.notify import create_notification, email_patient, get_hospital

router = APIRouter(tags=["billing"])

METHOD_LABELS = {"upi": "UPI", "card": "Credit / Debit Card", "netbanking": "Net Banking", "wallet": "Wallet", "cash": "Cash at Hospital"}
UPI_APPS = {"gpay": "Google Pay", "phonepe": "PhonePe", "paytm": "Paytm", "other": "Other UPI"}


def own_or_staff(user: dict, extra: dict) -> dict:
    if user["role"] == "patient":
        extra = {**extra, "patient_id": user["username"]}
    elif user["role"] not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Not allowed")
    return scoped(user["hospital_id"], extra)


@router.get("/invoices")
async def list_invoices(user: dict = Depends(get_current_user), status: Optional[str] = None):
    require_db()
    q = own_or_staff(user, {"status": status} if status else {})
    return {"invoices": serialize(await invoices_collection.find(q).sort("created_at", -1).to_list(500))}


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    require_db()
    inv = await invoices_collection.find_one(own_or_staff(user, {"invoice_id": invoice_id}))
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    appt = await appointments_collection.find_one({"appointment_id": inv["appointment_id"], "hospital_id": inv["hospital_id"]})
    pays = await payments_collection.find({"invoice_id": invoice_id}).sort("created_at", -1).to_list(50)
    h = await get_hospital(inv["hospital_id"])
    return {"invoice": serialize(inv), "appointment": serialize(appt), "payments": serialize(pays),
            "hospital": {k: h.get(k) for k in ("name", "address", "phone", "email")},
            "online_payments_enabled": gw.configured()}


class LineItem(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    amount: float = Field(ge=0)


class InvoiceUpdate(BaseModel):
    items: List[LineItem]


@router.patch("/admin/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, payload: InvoiceUpdate, user: dict = Depends(require_staff)):
    inv = await invoices_collection.find_one(scoped(user["hospital_id"], {"invoice_id": invoice_id}))
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv["status"] not in ("pending", "failed"):
        raise HTTPException(status_code=409, detail="Only unpaid invoices can be edited")
    items = [i.model_dump() for i in payload.items]
    await invoices_collection.update_one({"_id": inv["_id"]}, {"$set": {"items": items, "total": round(sum(i["amount"] for i in items), 2), "updated_at": now()}})
    return {"invoice": serialize(await invoices_collection.find_one({"_id": inv["_id"]}))}


@router.get("/payments")
async def list_payments(user: dict = Depends(get_current_user)):
    require_db()
    return {"payments": serialize(await payments_collection.find(own_or_staff(user, {})).sort("created_at", -1).to_list(500))}


# ----------------------------------------------------------------------------- state changes
async def _context(payment: dict):
    inv = await invoices_collection.find_one({"invoice_id": payment["invoice_id"]})
    patient = await patients_collection.find_one({"patient_id": payment["patient_id"]})
    return inv, patient


async def mark_paid(payment: dict, transaction_id: str, gateway_method: str = None):
    if payment.get("status") == "paid":
        return payment  # idempotent: webhook + client verify may both arrive
    upd = {"status": "paid", "transaction_id": transaction_id, "paid_at": now(), "updated_at": now()}
    if gateway_method:
        upd["gateway_method"] = gateway_method
    await payments_collection.update_one({"_id": payment["_id"]}, {"$set": upd})
    await invoices_collection.update_one({"invoice_id": payment["invoice_id"]}, {"$set": {"status": "paid", "paid_at": now(), "payment_id": payment["payment_id"], "updated_at": now()}})
    payment = await payments_collection.find_one({"_id": payment["_id"]})
    inv, patient = await _context(payment)
    params = {"amount": f"{payment['amount']:,.2f}", "invoice_id": inv["invoice_id"], "patient_name": inv.get("patient_name")}
    hid = payment["hospital_id"]
    await create_notification(hospital_id=hid, audience="patient", patient_id=payment["patient_id"], ntype="payment_success", params=params, link=f"/account/billing/{inv['invoice_id']}")
    await create_notification(hospital_id=hid, audience="admin", ntype="payment_received", params=params, link="/admin/billing")
    await email_patient("payment_success", hospital_id=hid, patient=patient, invoice=inv, payment=payment)
    return payment


async def mark_failed(payment: dict, reason: str = None, gateway_payment_id: str = None):
    if payment.get("status") in ("failed", "paid", "refunded"):
        return payment
    await payments_collection.update_one({"_id": payment["_id"]}, {"$set": {"status": "failed", "failure_reason": reason,
                                                                            "gateway_payment_id": gateway_payment_id, "updated_at": now()}})
    payment = await payments_collection.find_one({"_id": payment["_id"]})
    inv, patient = await _context(payment)
    params = {"amount": f"{payment['amount']:,.2f}", "invoice_id": inv["invoice_id"], "patient_name": inv.get("patient_name")}
    hid = payment["hospital_id"]
    await create_notification(hospital_id=hid, audience="patient", patient_id=payment["patient_id"], ntype="payment_failed", params=params, link=f"/account/billing/{inv['invoice_id']}")
    await create_notification(hospital_id=hid, audience="admin", ntype="payment_failed_admin", params=params, link="/admin/billing")
    await email_patient("payment_failed", hospital_id=hid, patient=patient, invoice=inv, payment=payment, extra={"reason": reason})
    return payment


async def mark_refunded(payment: dict, refund_id: str, refund_amount: float):
    if payment.get("status") == "refunded":
        return payment
    await payments_collection.update_one({"_id": payment["_id"]}, {"$set": {"status": "refunded", "refund_id": refund_id, "refund_amount": refund_amount,
                                                                            "refund_status": "processed", "refunded_at": now(), "updated_at": now()}})
    await invoices_collection.update_one({"invoice_id": payment["invoice_id"]}, {"$set": {"status": "refunded", "updated_at": now()}})
    payment = await payments_collection.find_one({"_id": payment["_id"]})
    inv, patient = await _context(payment)
    params = {"amount": f"{refund_amount:,.2f}", "invoice_id": inv["invoice_id"], "patient_name": inv.get("patient_name")}
    await create_notification(hospital_id=payment["hospital_id"], audience="patient", patient_id=payment["patient_id"], ntype="payment_refunded", params=params, link=f"/account/billing/{inv['invoice_id']}")
    await email_patient("payment_refunded", hospital_id=payment["hospital_id"], patient=patient, invoice=inv, payment=payment)
    return payment


# ----------------------------------------------------------------------------- patient pays
class OrderRequest(BaseModel):
    # extra="forbid": card numbers / CVV can never be posted to this API, even by mistake
    model_config = ConfigDict(extra="forbid")
    invoice_id: str
    method: Literal["upi", "card", "netbanking", "wallet", "cash"]
    upi_app: Optional[Literal["gpay", "phonepe", "paytm", "other"]] = None


@router.post("/payments/order")
async def create_payment(payload: OrderRequest, user: dict = Depends(require_patient)):
    require_db()
    inv = await invoices_collection.find_one(scoped(user["hospital_id"], {"invoice_id": payload.invoice_id, "patient_id": user["patient_id"]}))
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv["status"] not in ("pending", "failed"):
        raise HTTPException(status_code=409, detail=f"This invoice is {inv['status']}")
    if inv["total"] <= 0:
        raise HTTPException(status_code=409, detail="Nothing to pay on this invoice")
    patient = await patients_collection.find_one({"patient_id": user["patient_id"]})
    label = METHOD_LABELS[payload.method] + (f" — {UPI_APPS[payload.upi_app]}" if payload.upi_app else "")
    pay = {"payment_id": short_id("PAY-"), "hospital_id": inv["hospital_id"], "patient_id": inv["patient_id"], "patient_name": inv["patient_name"],
           "invoice_id": inv["invoice_id"], "appointment_id": inv["appointment_id"], "amount": inv["total"], "currency": "INR",
           "method": payload.method, "upi_app": payload.upi_app, "method_label": label, "status": "pending",
           "transaction_id": None, "created_at": now(), "updated_at": now()}

    if payload.method == "cash":
        pay["gateway"] = "cash"
        await payments_collection.insert_one(pay)
        await create_notification(hospital_id=inv["hospital_id"], audience="admin", ntype="cash_payment_selected", link="/admin/billing",
                                  params={"amount": f"{inv['total']:,.2f}", "invoice_id": inv["invoice_id"], "patient_name": inv["patient_name"]})
        return {"mode": "cash", "payment": serialize(pay)}

    if not gw.configured():
        raise HTTPException(status_code=503, detail="Online payments are not set up for this hospital yet. Please choose Cash at Hospital or try again later.")
    order = await gw.create_order(inv["total"], receipt=pay["payment_id"], notes={"invoice_id": inv["invoice_id"], "hospital_id": inv["hospital_id"]})
    pay.update({"gateway": "razorpay", "gateway_order_id": order["id"]})
    await payments_collection.insert_one(pay)
    hospital = await get_hospital(inv["hospital_id"])
    return {"mode": "razorpay", "payment": serialize(pay), "key_id": gw.key_id(), "order_id": order["id"], "amount": order["amount"],
            "currency": order["currency"], "name": hospital.get("name"), "description": f"Invoice {inv['invoice_id']}",
            "prefill": {"name": patient.get("full_name"), "email": patient.get("email"), "contact": patient.get("phone")}}


class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/payments/verify")
async def verify_payment(payload: VerifyRequest, user: dict = Depends(require_patient)):
    pay = await payments_collection.find_one({"gateway_order_id": payload.razorpay_order_id, "patient_id": user["patient_id"]})
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
    if not gw.verify_checkout_signature(payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment signature could not be verified")
    gp = await gw.fetch_payment(payload.razorpay_payment_id)  # ask the gateway, never trust the browser
    if gp.get("order_id") != payload.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Payment does not belong to this order")
    if gp.get("status") == "captured":
        pay = await mark_paid(pay, gp["id"], gp.get("method"))
    elif gp.get("status") == "failed":
        pay = await mark_failed(pay, gp.get("error_description"), gp["id"])
    else:  # authorized / created — the payment.captured webhook will finish it
        await payments_collection.update_one({"_id": pay["_id"]}, {"$set": {"gateway_payment_id": gp["id"], "updated_at": now()}})
        pay = await payments_collection.find_one({"_id": pay["_id"]})
    return {"payment": serialize(pay)}


class FailedReport(BaseModel):
    razorpay_order_id: str


@router.post("/payments/failed")
async def report_failed(payload: FailedReport, user: dict = Depends(require_patient)):
    """Called when checkout reports a failure; the status is re-checked with Razorpay first."""
    pay = await payments_collection.find_one({"gateway_order_id": payload.razorpay_order_id, "patient_id": user["patient_id"]})
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
    items = await gw.fetch_order_payments(payload.razorpay_order_id)
    if any(i.get("status") == "captured" for i in items):
        cap = next(i for i in items if i.get("status") == "captured")
        return {"payment": serialize(await mark_paid(pay, cap["id"], cap.get("method")))}
    failed = [i for i in items if i.get("status") == "failed"]
    if failed:
        pay = await mark_failed(pay, failed[-1].get("error_description"), failed[-1]["id"])
    return {"payment": serialize(pay)}


@router.post("/payments/webhook/razorpay")
async def razorpay_webhook(request: Request):
    body = await request.body()
    if not gw.verify_webhook_signature(body, request.headers.get("X-Razorpay-Signature")):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    event = json.loads(body)
    kind = event.get("event")
    ent = (event.get("payload", {}).get("payment") or {}).get("entity") or {}
    if kind in ("payment.captured", "payment.failed") and ent.get("order_id"):
        pay = await payments_collection.find_one({"gateway_order_id": ent["order_id"]})
        if pay:
            if kind == "payment.captured":
                await mark_paid(pay, ent["id"], ent.get("method"))
            else:
                await mark_failed(pay, ent.get("error_description"), ent["id"])
    elif kind == "refund.processed":
        ref = event["payload"]["refund"]["entity"]
        pay = await payments_collection.find_one({"transaction_id": ref.get("payment_id")})
        if pay:
            await mark_refunded(pay, ref["id"], ref.get("amount", 0) / 100)
    return {"received": True}


# ----------------------------------------------------------------------------- admin actions
@router.post("/admin/payments/{payment_id}/mark-paid")
async def cash_received(payment_id: str, user: dict = Depends(require_staff)):
    pay = await payments_collection.find_one(scoped(user["hospital_id"], {"payment_id": payment_id}))
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
    if pay.get("method") != "cash":
        raise HTTPException(status_code=409, detail="Online payments are confirmed by the payment gateway")
    return {"payment": serialize(await mark_paid(pay, f"CASH-{short_id()}"))}


class RefundRequest(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    reason: Optional[str] = None


@router.post("/admin/payments/{payment_id}/refund")
async def refund(payment_id: str, payload: RefundRequest, user: dict = Depends(require_staff)):
    pay = await payments_collection.find_one(scoped(user["hospital_id"], {"payment_id": payment_id}))
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
    if pay.get("status") != "paid":
        raise HTTPException(status_code=409, detail="Only paid payments can be refunded")
    amount = min(payload.amount or pay["amount"], pay["amount"])
    if pay.get("method") == "cash":
        return {"payment": serialize(await mark_refunded(pay, f"CASHREF-{short_id()}", amount))}
    if not gw.configured():
        raise HTTPException(status_code=503, detail="Payment gateway is not configured")
    r = await gw.refund(pay["transaction_id"], amount)
    if r.get("status") == "processed":
        return {"payment": serialize(await mark_refunded(pay, r["id"], amount))}
    await payments_collection.update_one({"_id": pay["_id"]}, {"$set": {"refund_id": r["id"], "refund_status": r.get("status", "pending"), "updated_at": now()}})
    return {"payment": serialize(await payments_collection.find_one({"_id": pay["_id"]})), "message": "Refund initiated; it will complete when the gateway processes it."}
