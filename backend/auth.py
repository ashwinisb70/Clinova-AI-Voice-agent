import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_to_a_random_secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
PATIENT_TOKEN_EXPIRE_MINUTES = int(os.getenv("PATIENT_TOKEN_EXPIRE_MINUTES", str(60 * 24)))
DEFAULT_HOSPITAL_ID = os.getenv("DEFAULT_HOSPITAL_ID", "CITY001")

STAFF_ROLES = ("admin", "staff")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(username: str, role: str = "staff", hospital_id: Optional[str] = None,
                        expires_minutes: Optional[int] = None) -> str:
    """`username` is the staff username, or the patient_id for patients."""
    minutes = expires_minutes or (PATIENT_TOKEN_EXPIRE_MINUTES if role == "patient" else ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": username, "role": role, "hid": hospital_id or DEFAULT_HOSPITAL_ID, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def _user_from_payload(payload: dict) -> dict:
    return {
        "username": payload.get("sub"),
        "role": payload.get("role"),
        # tokens issued before multi-tenancy have no hid → default tenant
        "hospital_id": payload.get("hid") or DEFAULT_HOSPITAL_ID,
    }


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return _user_from_payload(decode_access_token(credentials.credentials))


def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> Optional[dict]:
    if not credentials:
        return None
    return _user_from_payload(decode_access_token(credentials.credentials))


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_staff(user: dict = Depends(get_current_user)) -> dict:
    """Hospital staff or admin. Patients are always rejected."""
    if user.get("role") not in STAFF_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital staff access required")
    return user


def require_patient(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient login required")
    return {**user, "patient_id": user["username"]}
