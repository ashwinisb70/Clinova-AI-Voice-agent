import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "vextracore_voice_agent")

if MONGODB_URI == "mongomock://":
    # Local testing only: in-memory MongoDB (pip install mongomock-motor). Never use in production.
    from mongomock_motor import AsyncMongoMockClient
    client = AsyncMongoMockClient()
elif MONGODB_URI:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
else:
    client = None

db = client[MONGODB_DB_NAME] if client is not None else None

# Existing collections (unchanged names)
patients_collection = db["patients"] if db is not None else None
appointments_collection = db["appointments"] if db is not None else None
faqs_collection = db["faqs"] if db is not None else None
call_logs_collection = db["call_logs"] if db is not None else None
escalations_collection = db["escalations"] if db is not None else None
users_collection = db["users"] if db is not None else None

# New collections (MediAssist SaaS)
hospitals_collection = db["hospitals"] if db is not None else None
departments_collection = db["departments"] if db is not None else None
doctors_collection = db["doctors"] if db is not None else None
invoices_collection = db["invoices"] if db is not None else None
payments_collection = db["payments"] if db is not None else None
notifications_collection = db["notifications"] if db is not None else None
email_logs_collection = db["email_logs"] if db is not None else None
conversations_collection = db["ai_conversations"] if db is not None else None
password_resets_collection = db["password_resets"] if db is not None else None


def get_db():
    if db is None:
        raise RuntimeError("MongoDB is not configured. Set MONGODB_URI in your .env file.")
    return db


def require_db():
    """Raise a clean HTTP 500 when MongoDB isn't configured."""
    if db is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Database not configured")
