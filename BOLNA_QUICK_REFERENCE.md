# BOLNA /book-appointment - Quick Reference

## EXACT SCHEMA

```python
# backend/models.py
class BookAppointmentRequest(BaseModel):
    patient_name: str                          # ✅ REQUIRED
    department: str                            # ✅ REQUIRED
    preferred_date: str                        # ✅ REQUIRED (YYYY-MM-DD)
    preferred_time: Optional[str] = None       # ⭕ OPTIONAL
    doctor_id: Optional[str] = None            # ⭕ OPTIONAL
    notes: Optional[str] = None                # ⭕ OPTIONAL
```

---

## MINIMAL VALID REQUEST

```json
POST /book-appointment HTTP/1.1
Content-Type: application/json
X-Agent-Key: {AGENT_API_KEY}
X-Hospital-Id: DEFAULT

{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05"
}
```

---

## COMPLETE VALID REQUEST

```json
POST /book-appointment HTTP/1.1
Content-Type: application/json
X-Agent-Key: {AGENT_API_KEY}
X-Hospital-Id: DEFAULT
X-Conversation-Id: {bolna_call_id}

{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05",
  "preferred_time": "11:00 AM",
  "doctor_id": "dr-sharma-1",
  "notes": "Follow-up checkup"
}
```

---

## COMMON 422 ERRORS

| Error Message | Cause | Fix |
|---------------|-------|-----|
| `Field required` | Missing required field (patient_name, department, or preferred_date) | Ensure all 3 required fields are in JSON body |
| `Input should be a valid string` | Sent number, date object, or null instead of string | Convert all fields to strings |
| `String should have at least 1 character` | Empty string `""` sent | Don't send empty strings for required fields |

---

## FIELD REQUIREMENTS

| Field | Required? | Type | Format | Example |
|-------|-----------|------|--------|---------|
| `patient_name` | ✅ YES | string | Non-empty | "Rajesh Kumar" |
| `department` | ✅ YES | string | Dept name | "Cardiology" |
| `preferred_date` | ✅ YES | string | YYYY-MM-DD | "2026-10-05" |
| `preferred_time` | ❌ NO | string\|null | HH:MM AM/PM | "11:00 AM" |
| `doctor_id` | ❌ NO | string\|null | Doctor ID | "dr-sharma-1" |
| `notes` | ❌ NO | string\|null | Any text | "Follow-up" |

---

## REQUIRED HEADERS

```
X-Agent-Key: {value of AGENT_API_KEY from backend/.env}
X-Hospital-Id: DEFAULT (or your hospital ID)
X-Conversation-Id: {bolna call ID} (optional, for call tracking)
Content-Type: application/json
```

---

## SUCCESS RESPONSE

```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "message": "Appointment request received for Rajesh Kumar in Cardiology on 2026-10-05 at 11:00 AM. The hospital will confirm it shortly.",
  "appointment_id": "APT-abc123de",
  "status": "pending",
  "invoice_id": null,
  "email_queued": false
}
```

---

## DEBUGGING CHECKLIST

- [ ] All 3 required fields present in JSON: `patient_name`, `department`, `preferred_date`
- [ ] All fields are **strings**, not numbers or date objects
- [ ] `preferred_date` format is exactly **YYYY-MM-DD** (e.g., "2026-10-05")
- [ ] `preferred_time` format is **HH:MM AM/PM** (e.g., "11:00 AM") if included
- [ ] No null values for required fields
- [ ] Header `X-Agent-Key` is set and matches `AGENT_API_KEY` in backend/.env
- [ ] Header `Content-Type: application/json` is set
- [ ] HTTP method is **POST** (not GET, PUT, or PATCH)
- [ ] Endpoint URL is `https://your-backend/book-appointment`

---

## BACKEND LOGS TO LOOK FOR

### ✅ Success
```
[BOLNA DEBUG] POST /book-appointment received: patient_name='Rajesh Kumar', department='Cardiology', preferred_date='2026-10-05', preferred_time='11:00 AM', doctor_id=None, has_conversation_id=True
```

### ❌ Validation Error
```
[BOLNA DEBUG] POST /book-appointment validation error: body → patient_name: Field required (type: missing)
```

The error message tells you EXACTLY which field is missing or invalid.

---

## BOLNA TOOL CONFIG CHECKLIST

In Bolna's custom tool configuration:

- [ ] `http_config.method` = `"POST"`
- [ ] `http_config.url` = your backend `/book-appointment` endpoint
- [ ] Arguments include: `patient_name`, `department`, `preferred_date`
- [ ] Argument types: all `"type": "string"`
- [ ] `patient_name` is `"required": true`
- [ ] `department` is `"required": true`
- [ ] `preferred_date` is `"required": true`
- [ ] All date extractions convert to YYYY-MM-DD string format
- [ ] Headers include `X-Agent-Key` with AGENT_API_KEY value
- [ ] Headers include `Content-Type: application/json`

---

## WHAT CAUSES 422 (MOST COMMON)

### 🔴 Missing Required Field
```
Bolna doesn't extract patient_name → sends JSON without it → 422
```

### 🔴 Wrong Type
```
Bolna extracts date as object → sends {"preferred_date": Date(2026, 10, 5)} → 422
Should send: {"preferred_date": "2026-10-05"}
```

### 🔴 Wrong Date Format
```
Bolna sends "preferred_date": "Oct 5, 2026" → 422
Should send: "preferred_date": "2026-10-05"
```

### 🔴 Null for Required Field
```
Bolna can't extract department → sends {"department": null} → 422
Should validate extraction and ask user if not found
```

---

## AFTER FIX: VERIFY IN CLINOVA

1. Make a test Bolna call
2. Go to CLINOVA Appointments page
3. Look for your appointment with:
   - **Status:** PENDING (yellow badge)
   - **Patient:** Your name
   - **Department:** What you said
   - **Date:** Tomorrow or date you specified
   - **Source:** "voice" (if visible in UI)

---

**Full debug guide:** See `BOLNA_422_DEBUG_GUIDE.md`
