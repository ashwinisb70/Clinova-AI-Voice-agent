FAQ_KNOWLEDGE = {
    "visiting hours": (
        "General wards: 4:00 PM to 6:00 PM daily. ICU: 5:00 PM to 5:30 PM, "
        "immediate family only. Maternity ward: 10:00 AM to 12:00 PM and "
        "4:00 PM to 6:00 PM."
    ),
    "departments": (
        "Cardiology is on the 2nd floor of Block A. General Medicine is on "
        "the 1st floor of Block A. Orthopedics is on the 3rd floor of Block B. "
        "Pediatrics is on the ground floor of Block C. Gynecology is on the "
        "2nd floor of Block C. Emergency is on the ground floor of Block A, "
        "open 24/7."
    ),
    "insurance": (
        "We accept major insurance providers including Star Health, HDFC Ergo, "
        "ICICI Lombard, and government health schemes such as Ayushman Bharat. "
        "Please bring your insurance card and a valid photo ID at admission."
    ),
    "appointment": (
        "Appointments can be booked by phone, WhatsApp, or in person at the "
        "reception desk. Please arrive 15 minutes before your scheduled time."
    ),
    "policies": (
        "One attendant is allowed per patient in general wards. Mobile phones "
        "must be silent in ICU and NICU areas. Discharge typically takes "
        "2 to 3 hours after the doctor's clearance."
    ),
    "emergency": (
        "For medical emergencies, call our emergency line or visit the ER "
        "directly — it's open 24/7."
    ),
}


def find_faq_answer(question: str, topic: str = None) -> str:
    search_text = f"{topic or ''} {question}".lower()
    for keyword, answer in FAQ_KNOWLEDGE.items():
        if keyword in search_text:
            return answer
    return (
        "I don't have specific information on that. Let me connect you "
        "with our reception desk for further help."
    )
