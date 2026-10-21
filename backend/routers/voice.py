"""Call AI Receptionist.

- Patients can always dial the hospital's AI receptionist number (hospital.ai_receptionist_phone).
- Logged-in patients can request a callback: FastAPI asks Bolna to place an outbound call.
  Bolna credentials stay on the server: BOLNA_API_KEY, BOLNA_AGENT_ID, BOLNA_API_BASE.
"""
import os
import re
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import require_patient
from database import hospitals_collection, patients_collection
from services.common import request_hospital_id, now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


def bolna_configured():
    return bool(os.getenv("BOLNA_API_KEY") and os.getenv("BOLNA_AGENT_ID"))


@router.get("/config")
async def config(hospital_id: str = Depends(request_hospital_id)):
    h = await hospitals_collection.find_one({"hospital_id": hospital_id}) if hospitals_collection is not None else None
    return {"dial_number": (h or {}).get("ai_receptionist_phone") or None, "callback_enabled": bolna_configured()}


class CallRequest(BaseModel):
    phone: str


@router.post("/call")
async def request_call(payload: CallRequest, user: dict = Depends(require_patient)):
    if not bolna_configured():
        raise HTTPException(status_code=503, detail="The AI receptionist callback service is not configured on the server")
    phone = re.sub(r"[\s\-()]", "", payload.phone)
    if not re.match(r"^\+?[0-9]{10,13}$", phone):
        raise HTTPException(status_code=422, detail="Enter a valid phone number")
    if not phone.startswith("+"):
        phone = "+91" + phone[-10:]
    patient = await patients_collection.find_one({"patient_id": user["patient_id"]})
    base = os.getenv("BOLNA_API_BASE", "https://api.bolna.ai").rstrip("/")
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{base}/call", headers={"Authorization": f"Bearer {os.getenv('BOLNA_API_KEY')}"},
                         json={"agent_id": os.getenv("BOLNA_AGENT_ID"), "recipient_phone_number": phone,
                               "user_data": {"patient_name": (patient or {}).get("full_name"), "patient_id": user["patient_id"],
                                             "hospital_id": user["hospital_id"], "requested_at": now().isoformat()}})
    if r.status_code >= 400:
        try:
            error_data = r.json()
            safe_error = error_data.get("detail") or error_data.get("message") or error_data.get("error") or "No safe error message returned"
            if not isinstance(safe_error, str):
                safe_error = "Bolna returned a structured error"
            safe_error = safe_error[:300]
        except (ValueError, TypeError):
            safe_error = "Bolna returned a non-JSON error response"

        logger.warning(
            "Bolna callback rejected request: HTTP %s; message=%s",
            r.status_code,
            safe_error
        )
        raise HTTPException(status_code=502, detail="The AI receptionist could not place the call. Check the backend terminal logs.")
    data = r.json() if r.content else {}
    return {"success": True, "call_id": data.get("execution_id") or data.get("call_id"), "status": data.get("status", "queued")}



