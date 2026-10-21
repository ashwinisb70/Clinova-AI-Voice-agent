"""Creates the default hospital tenant (City Hospital) on first start.

Hospital details come from environment variables so real contact data never lives in code.
Departments/doctors are only inserted when the hospital has none, so anything an admin
edits later is never overwritten. Replace them from Admin → Doctors / Departments.
"""
import os

from auth import DEFAULT_HOSPITAL_ID
from database import hospitals_collection, departments_collection, doctors_collection, patients_collection, notifications_collection, appointments_collection, invoices_collection, payments_collection, conversations_collection, email_logs_collection
from services.common import now

U = lambda pid, w=800: f"https://images.unsplash.com/photo-{pid}?auto=format&fit=crop&w={w}&q=80"  # noqa: E731


def hospital_defaults():
    return {
        "hospital_id": DEFAULT_HOSPITAL_ID,
        "name": os.getenv("HOSPITAL_NAME", "City Hospital"),
        "tagline": os.getenv("HOSPITAL_TAGLINE", "Quality Care. Always."),
        "address": os.getenv("HOSPITAL_ADDRESS", "123 Health Street, Bengaluru, Karnataka 560001"),
        "city": os.getenv("HOSPITAL_CITY", "Bengaluru"),
        "phone": os.getenv("HOSPITAL_PHONE", "+91 98765 43210"),
        "email": os.getenv("HOSPITAL_EMAIL", "contact@cityhospital.com"),
        "emergency_phone": os.getenv("HOSPITAL_EMERGENCY_PHONE", "108"),
        "timings": [
            {"days": os.getenv("HOSPITAL_DAYS", "Monday – Saturday"), "hours": os.getenv("HOSPITAL_HOURS", "8:00 AM – 8:00 PM")},
            {"days": "Sunday", "hours": os.getenv("HOSPITAL_SUNDAY_HOURS", "9:00 AM – 2:00 PM")},
        ],
        "latitude": float(os.getenv("HOSPITAL_LATITUDE", "12.9716")),
        "longitude": float(os.getenv("HOSPITAL_LONGITUDE", "77.5946")),
        "ai_receptionist_phone": os.getenv("AI_RECEPTIONIST_PHONE", ""),
        "currency": "INR",
        "created_at": now(),
    }


DEPARTMENTS = [
    ("cardiology", "Cardiology", 800), ("pediatrics", "Pediatrics", 600), ("neurology", "Neurology", 900),
    ("orthopedics", "Orthopedics", 700), ("dermatology", "Dermatology", 600), ("general-medicine", "General Medicine", 500),
    ("diagnostics", "Diagnostics", 400),
]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

DOCTORS = [
    ("rahul-sharma", "Dr. Rahul Sharma", "Cardiology", "cardiology", 12, "MBBS, MD (Cardiology)", "1622253692010-333f2da6031d", 1000, "9:00 AM – 5:00 PM",
     "Dr. Rahul Sharma is a cardiologist focused on preventive cardiology, hypertension and heart-failure management."),
    ("priya-nair", "Dr. Priya Nair", "Dermatology", "dermatology", 10, "MBBS, MD (Dermatology)", "1559839734-2b71ea197ec2", 700, "10:00 AM – 4:00 PM",
     "Dr. Priya Nair specialises in medical and cosmetic dermatology, including acne, pigmentation and hair disorders."),
    ("arjun-rao", "Dr. Arjun Rao", "Orthopedics", "orthopedics", 14, "MBBS, MS (Orthopaedics)", "1612349317150-e413f6a5b16d", 800, "9:00 AM – 5:00 PM",
     "Dr. Arjun Rao treats bone, joint and sports injuries, with extensive experience in fracture care and rehabilitation."),
    ("ananya-mehta", "Dr. Ananya Mehta", "General Medicine", "general-medicine", 11, "MBBS, MD (General Medicine)", "1594824476967-48c8b964273f", 600, "9:00 AM – 4:00 PM",
     "Dr. Ananya Mehta provides primary care for adults, from routine check-ups to diabetes and thyroid management."),
    ("kavya-reddy", "Dr. Kavya Reddy", "Pediatrics", "pediatrics", 9, "MBBS, MD (Pediatrics)", "1651008376811-b90baee60c1f", 700, "9:00 AM – 3:00 PM",
     "Dr. Kavya Reddy cares for infants, children and adolescents, including growth monitoring and vaccinations."),
    ("vikram-desai", "Dr. Vikram Desai", "Radiology", "diagnostics", 13, "MBBS, MD (Radiodiagnosis)", "1582750433449-648ed127bb54", 500, "8:00 AM – 4:00 PM",
     "Dr. Vikram Desai leads diagnostics, overseeing imaging and laboratory services."),
]


async def ensure_indexes():
    try:
        await patients_collection.create_index([("hospital_id", 1), ("email", 1)], unique=True)
        await patients_collection.create_index([("hospital_id", 1), ("phone", 1)], unique=True)
        for col, key in ((appointments_collection, "appointment_id"), (invoices_collection, "invoice_id"), (payments_collection, "payment_id"),
                         (conversations_collection, "conversation_id"), (email_logs_collection, "email_id")):
            await col.create_index(key)
        await notifications_collection.create_index([("hospital_id", 1), ("audience", 1), ("patient_id", 1), ("created_at", -1)])
        await payments_collection.create_index("gateway_order_id")
    except Exception:  # noqa: BLE001 — index creation must never block startup
        pass


async def seed_default_tenant():
    if hospitals_collection is None:
        return
    await ensure_indexes()
    if not await hospitals_collection.find_one({"hospital_id": DEFAULT_HOSPITAL_ID}):
        await hospitals_collection.insert_one(hospital_defaults())
    hid = DEFAULT_HOSPITAL_ID
    if await departments_collection.count_documents({"hospital_id": hid}) == 0:
        await departments_collection.insert_many([
            {"hospital_id": hid, "department_id": slug, "name": name, "consultation_fee": fee, "active": True, "created_at": now()}
            for slug, name, fee in DEPARTMENTS])
    if await doctors_collection.count_documents({"hospital_id": hid}) == 0:
        await doctors_collection.insert_many([
            {"hospital_id": hid, "doctor_id": did, "name": name, "specialization": spec, "department_id": dept,
             "department": next(n for s, n, _ in DEPARTMENTS if s == dept), "experience_years": yrs, "qualifications": q,
             "photo_url": U(photo), "consultation_fee": fee, "available": True, "about": about,
             "schedule": [{"day": d, "hours": "9:00 AM – 1:00 PM" if d == "Saturday" else hours} for d in WEEKDAYS],
             "created_at": now()}
            for did, name, spec, dept, yrs, q, photo, fee, hours, about in DOCTORS])
