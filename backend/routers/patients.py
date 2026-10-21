"""Patient accounts: register, login, profile, forgot/reset password."""
import hashlib
import re
import secrets
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

from auth import create_access_token, hash_password, verify_password, require_patient
from database import patients_collection, password_resets_collection, hospitals_collection, require_db
from services.common import now, short_id, serialize, request_hospital_id
from services.notify import create_notification, email_patient
from services.email_templates import FRONTEND_URL

router = APIRouter(prefix="/patients", tags=["patients"])

PHONE_RE = re.compile(r"^\+?[0-9]{10,13}$")
LANGS = ("en", "kn", "hi")


def norm_phone(p: str) -> str:
    return re.sub(r"[\s\-()]", "", p or "")


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    phone: str
    password: str = Field(min_length=8, max_length=128)
    language: Optional[str] = "en"

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        v = norm_phone(v)
        if not PHONE_RE.match(v):
            raise ValueError("Enter a valid phone number")
        return v


class PatientLogin(BaseModel):
    identifier: str  # email or phone
    password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    phone: Optional[str] = None
    language: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None


class ForgotRequest(BaseModel):
    email: EmailStr


class ResetRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


def public_patient(p: dict) -> dict:
    d = serialize(p)
    d.pop("_id", None)
    return d


def token_response(p: dict) -> dict:
    return {"access_token": create_access_token(p["patient_id"], role="patient", hospital_id=p["hospital_id"]),
            "token_type": "bearer", "patient": public_patient(p)}


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest, hospital_id: str = Depends(request_hospital_id)):
    require_db()
    if not await hospitals_collection.find_one({"hospital_id": hospital_id}):
        raise HTTPException(status_code=404, detail="Hospital not found")
    email = payload.email.lower()
    if await patients_collection.find_one({"hospital_id": hospital_id, "email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    if await patients_collection.find_one({"hospital_id": hospital_id, "phone": payload.phone}):
        raise HTTPException(status_code=409, detail="An account with this phone number already exists")
    doc = {"patient_id": short_id("PAT-"), "hospital_id": hospital_id, "full_name": payload.full_name.strip(),
           "email": email, "phone": payload.phone, "password_hash": hash_password(payload.password),
           "language": payload.language if payload.language in LANGS else "en", "created_at": now()}
    await patients_collection.insert_one(doc)
    await create_notification(hospital_id=hospital_id, audience="admin", ntype="new_patient",
                              params={"patient_name": doc["full_name"]}, link="/admin/patients")
    await email_patient("registration", hospital_id=hospital_id, patient=doc)
    return token_response(doc)


@router.post("/login")
async def login(payload: PatientLogin, hospital_id: str = Depends(request_hospital_id)):
    require_db()
    ident = payload.identifier.strip()
    query = {"email": ident.lower()} if "@" in ident else {"phone": norm_phone(ident)}
    p = await patients_collection.find_one({"hospital_id": hospital_id, **query})
    if not p or not p.get("password_hash") or not verify_password(payload.password, p["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email/phone or password")
    return token_response(p)


@router.get("/me")
async def me(user: dict = Depends(require_patient)):
    require_db()
    p = await patients_collection.find_one({"patient_id": user["patient_id"], "hospital_id": user["hospital_id"]})
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"patient": public_patient(p)}


@router.put("/me")
async def update_me(payload: ProfileUpdate, user: dict = Depends(require_patient)):
    require_db()
    changes = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "phone" in changes:
        changes["phone"] = norm_phone(changes["phone"])
        if not PHONE_RE.match(changes["phone"]):
            raise HTTPException(status_code=422, detail="Enter a valid phone number")
        clash = await patients_collection.find_one({"hospital_id": user["hospital_id"], "phone": changes["phone"],
                                                    "patient_id": {"$ne": user["patient_id"]}})
        if clash:
            raise HTTPException(status_code=409, detail="An account with this phone number already exists")
    if "language" in changes and changes["language"] not in LANGS:
        changes.pop("language")
    changes["updated_at"] = now()
    await patients_collection.update_one({"patient_id": user["patient_id"]}, {"$set": changes})
    return await me(user)


@router.post("/me/password")
async def change_password(payload: ChangePassword, user: dict = Depends(require_patient)):
    p = await patients_collection.find_one({"patient_id": user["patient_id"]})
    if not p or not verify_password(payload.current_password, p["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    await patients_collection.update_one({"patient_id": p["patient_id"]}, {"$set": {"password_hash": hash_password(payload.new_password)}})
    return {"success": True}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotRequest, hospital_id: str = Depends(request_hospital_id)):
    """Always returns the same response so the endpoint can't be used to discover accounts."""
    require_db()
    p = await patients_collection.find_one({"hospital_id": hospital_id, "email": payload.email.lower()})
    if p:
        raw = secrets.token_urlsafe(32)
        await password_resets_collection.insert_one({
            "token_hash": hashlib.sha256(raw.encode()).hexdigest(), "patient_id": p["patient_id"],
            "hospital_id": hospital_id, "expires_at": now() + timedelta(minutes=30), "used": False, "created_at": now()})
        await email_patient("password_reset", hospital_id=hospital_id, patient=p,
                            extra={"reset_url": f"{FRONTEND_URL}/reset-password?token={raw}"})
    return {"success": True, "message": "If an account exists for this email, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(payload: ResetRequest):
    require_db()
    rec = await password_resets_collection.find_one({"token_hash": hashlib.sha256(payload.token.encode()).hexdigest(), "used": False})
    exp = rec and rec["expires_at"]
    if exp is not None and exp.tzinfo is None:
        from datetime import timezone
        exp = exp.replace(tzinfo=timezone.utc)
    if not rec or exp < now():
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")
    await patients_collection.update_one({"patient_id": rec["patient_id"]}, {"$set": {"password_hash": hash_password(payload.password)}})
    await password_resets_collection.update_one({"_id": rec["_id"]}, {"$set": {"used": True}})
    return {"success": True}
