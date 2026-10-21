"""Razorpay integration (server side only). Keys come from the environment:

RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET

Card numbers / CVV are entered inside Razorpay Checkout and go straight to Razorpay —
they never reach this server or the database.
"""
import hashlib
import hmac
import os

import httpx

API = "https://api.razorpay.com/v1"


def key_id():
    return os.getenv("RAZORPAY_KEY_ID")


def configured() -> bool:
    return bool(os.getenv("RAZORPAY_KEY_ID") and os.getenv("RAZORPAY_KEY_SECRET"))


def _auth():
    return (os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))


async def create_order(amount_rupees: float, receipt: str, notes: dict) -> dict:
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{API}/orders", auth=_auth(), json={
            "amount": int(round(amount_rupees * 100)), "currency": "INR", "receipt": receipt[:40], "notes": notes})
    r.raise_for_status()
    return r.json()


async def fetch_payment(payment_id: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{API}/payments/{payment_id}", auth=_auth())
    r.raise_for_status()
    return r.json()


async def fetch_order_payments(order_id: str) -> list:
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{API}/orders/{order_id}/payments", auth=_auth())
    r.raise_for_status()
    return r.json().get("items", [])


async def refund(payment_id: str, amount_rupees: float = None) -> dict:
    body = {"amount": int(round(amount_rupees * 100))} if amount_rupees else {}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{API}/payments/{payment_id}/refund", auth=_auth(), json=body)
    r.raise_for_status()
    return r.json()


def verify_checkout_signature(order_id: str, payment_id: str, signature: str) -> bool:
    secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    expected = hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
    return bool(secret) and hmac.compare_digest(expected, signature or "")


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return bool(secret) and hmac.compare_digest(expected, signature or "")
