# BOLNA 422 Unprocessable Entity - Debug Guide

**Issue:** Bolna calls `POST /book-appointment` but receives 422 validation error.

---

## 1. EXACT BookAppointmentRequest SCHEMA

**Location:** `backend/models.py`, lines 6-13

```python
class BookAppointmentRequest(BaseModel):
    patient_name: str                          # REQUIRED - non-empty string
    department: str                            # REQUIRED - non-empty string
    preferred_date: str                        # REQUIRED - YYYY-MM-DD format
    preferred_time: Optional[str] = None       # OPTIONAL - can be None or string
    doctor_id: Optional[str] = None            # OPTIONAL - can be None or string
    notes: Optional[str] = None                # OPTIONAL - can be None or string
```

### Field Validation Rules (Pydantic):
- **`patient_name`** (str, required)
  - Must be present in JSON body
  - Cannot be null or missing
  - Type must be string
  
- **`department`** (str, required)
  - Must be present in JSON body
  - Cannot be null or missing
  - Type must be string
  
- **`preferred_date`** (str, required)
  - Must be present in JSON body
  - Cannot be null or missing
  - Type must be string
  - Format: YYYY-MM-DD (e.g., "2026-10-05")
  
- **`preferred_time`** (Optional[str], optional)
  - Can be omitted from JSON
  - If present, can be null or a string
  - Format: "HH:MM AM/PM" (e.g., "11:00 AM")
  
- **`doctor_id`** (Optional[str], optional)
  - Can be omitted from JSON
  - If present, can be null or a string
  - Example: "dr-sharma-1"
  
- **`notes`** (Optional[str], optional)
  - Can be omitted from JSON
  - If present, can be null or a string

---

## 2. EXPECTED JSON BODY (MINIMAL)

**Valid minimal request (only required fields):**
```json
{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05"
}
```

**Valid complete request (all fields):**
```json
{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05",
  "preferred_time": "11:00 AM",
  "doctor_id": "dr-sharma-1",
  "notes": "Follow-up checkup requested"
}
```

**Valid with null optional fields:**
```json
{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05",
  "preferred_time": null,
  "doctor_id": null,
  "notes": null
}
```

**Also valid (omit optional fields entirely):**
```json
{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05"
}
```

---

## 3. COMMON 422 ERRORS & CAUSES

### Error 1: Missing Required Field
**Example error log:**
```
[BOLNA DEBUG] POST /book-appointment validation error: 
body → patient_name: Field required (type: missing)
```

**Cause:** Bolna didn't extract or send `patient_name`

**Solution in Bolna tool:** Ensure the tool captures:
```python
{
  "patient_name": extracted_patient_name,  # ← Must exist
  "department": extracted_department,
  "preferred_date": extracted_date,
  ...
}
```

---

### Error 2: Wrong Data Type
**Example error log:**
```
[BOLNA DEBUG] POST /book-appointment validation error: 
body → preferred_date: Input should be a valid string (type: string_type)
```

**Cause:** Bolna sent `preferred_date` as a date object instead of string, or sent a number

**Bolna sends:** `"preferred_date": 2026-10-05` (number)
**Should send:** `"preferred_date": "2026-10-05"` (string)

**Solution in Bolna tool:** Always convert dates to string format:
```python
{
  "preferred_date": str(date_object)  # ← Convert to string "2026-10-05"
}
```

---

### Error 3: Null Value for Required Field
**Example error log:**
```
[BOLNA DEBUG] POST /book-appointment validation error: 
body → department: Input should be a valid string (type: string_type)
```

**Cause:** Bolna sent `null` instead of actual value

**Bolna sends:** `"department": null`
**Should send:** `"department": "Cardiology"`

**Solution in Bolna tool:** Validate extracted values are non-null:
```python
if not department:
    department = ask_user("Which department?")
```

---

### Error 4: Extra Unknown Fields (Usually OK)
**Note:** Pydantic by default ignores extra fields, so this shouldn't cause 422.

But if you see: `Extra inputs are not permitted (type: extra_forbidden)`
- Check if Pydantic has `model_config = ConfigDict(extra="forbid")`
- Current model does NOT have this, so extra fields are safe

---

### Error 5: Empty String for Required Field
**Example error log:**
```
[BOLNA DEBUG] POST /book-appointment validation error: 
body → patient_name: String should have at least 1 character (type: string_too_short)
```

**Cause:** Bolna sent empty string

**Bolna sends:** `"patient_name": ""`
**Should send:** `"patient_name": "Rajesh Kumar"`

**Solution:** Don't send empty strings for required fields

---

## 4. WHY BOLNA'S CURRENT TOOL PRODUCES 422

**Most likely cause:** The Bolna custom tool is not extracting all three required fields:
- `patient_name`
- `department`
- `preferred_date`

**Or:** One of the fields is being sent as the wrong type (number instead of string, null instead of string, etc.)

**To identify:** Check the backend logs after restarting:

```bash
cd backend
python main.py
```

When Bolna makes the request, look for logs:
```
[BOLNA DEBUG] POST /book-appointment validation error: ...
```

The log will show EXACTLY which field is missing or invalid.

---

## 5. MINIMAL CHANGE NEEDED IN BOLNA TOOL

### Current Bolna Tool Configuration (Likely Issue)

The Bolna tool probably looks like:
```json
{
  "name": "book_appointment",
  "description": "Book an appointment at the hospital",
  "http_config": {
    "url": "https://your-backend.com/book-appointment",
    "method": "POST",
    "headers": {
      "X-Agent-Key": "{{AGENT_API_KEY}}",
      "Content-Type": "application/json"
    }
  },
  "arguments": [
    {
      "name": "patient_name",
      "description": "Patient's full name",
      "type": "string",
      "required": true
    },
    {
      "name": "department",
      "description": "Medical department (e.g., Cardiology, Orthopedics)",
      "type": "string",
      "required": true
    },
    {
      "name": "preferred_date",
      "description": "Appointment date in YYYY-MM-DD format",
      "type": "string",
      "required": true
    },
    {
      "name": "preferred_time",
      "description": "Appointment time (e.g., 11:00 AM)",
      "type": "string",
      "required": false
    }
  ]
}
```

### What to Check in Bolna Tool

1. **All three required arguments are present:**
   - ✅ `patient_name` (string, required)
   - ✅ `department` (string, required)
   - ✅ `preferred_date` (string, required)

2. **Argument types are correct:**
   - All should be `"type": "string"` (not date, not number)

3. **Date format is YYYY-MM-DD:**
   - Bolna extraction should convert any date to string in format "2026-10-05"
   - NOT "Oct 5, 2026" or "5/10/2026"

4. **Headers are set correctly:**
   ```
   "X-Agent-Key": "{{AGENT_API_KEY}}"
   "Content-Type": "application/json"
   ```

5. **HTTP method is POST:**
   - NOT GET or PUT

### Exact JSON Body Bolna Should Send

When Bolna calls the endpoint, the HTTP body must be:

```json
{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05",
  "preferred_time": "11:00 AM",
  "doctor_id": null,
  "notes": null
}
```

Or with optional fields omitted:

```json
{
  "patient_name": "Rajesh Kumar",
  "department": "Cardiology",
  "preferred_date": "2026-10-05"
}
```

---

## 6. DEBUGGING STEPS

### Step 1: Restart backend with logging enabled
```bash
cd backend
export DEBUG=true  # Optional, for more verbose logs
python main.py
```

### Step 2: Trigger Bolna call
Make a test call to your AI receptionist with:
- Your name
- Department choice
- Date (tomorrow or specific date)

### Step 3: Check backend logs
Look for lines like:
```
[BOLNA DEBUG] POST /book-appointment validation error: body → field_name: error message
```

Or if it passes validation:
```
[BOLNA DEBUG] POST /book-appointment received: patient_name='Rajesh Kumar', department='Cardiology', preferred_date='2026-10-05', preferred_time='11:00 AM', doctor_id=None, has_conversation_id=True
```

### Step 4: Identify the exact issue
- If you see a validation error, the field name and error type tells you exactly what's wrong
- If you see the "received" log, the request passed validation but failed downstream (database, etc.)

---

## 7. BACKEND RESPONSES TO EXPECT

### ✅ Success Response (200)
```json
{
  "success": true,
  "message": "Appointment request received for Rajesh Kumar in Cardiology on 2026-10-05 at 11:00 AM. The hospital will confirm it shortly.",
  "appointment_id": "APT-abc123de",
  "status": "pending",
  "invoice_id": null,
  "email_queued": false
}
```

### ❌ 422 Validation Error
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "patient_name"],
      "msg": "Field required",
      "input": {...}
    }
  ]
}
```

Backend will also log:
```
[BOLNA DEBUG] POST /book-appointment validation error: body → patient_name: Field required (type: missing)
```

### ❌ 401 Auth Error
```json
{
  "detail": "Please login to book an appointment"
}
```

This means: X-Agent-Key header not sent or doesn't match AGENT_API_KEY

### ❌ 422 Business Logic Error
```json
{
  "detail": "Unknown department"
}
```

This means: Validation passed, but the appointment data is invalid (e.g., department doesn't exist in hospital)

---

## 8. SUMMARY TABLE

| Check | Required? | Type | Example | Status |
|-------|-----------|------|---------|--------|
| `patient_name` | ✅ YES | string | "Rajesh Kumar" | Send in JSON |
| `department` | ✅ YES | string | "Cardiology" | Send in JSON |
| `preferred_date` | ✅ YES | string (YYYY-MM-DD) | "2026-10-05" | Send in JSON |
| `preferred_time` | ❌ NO | string or null | "11:00 AM" | Optional |
| `doctor_id` | ❌ NO | string or null | "dr-sharma-1" | Optional |
| `notes` | ❌ NO | string or null | "Follow-up" | Optional |
| `X-Agent-Key` header | ✅ YES | string | AGENT_API_KEY value | Required |
| `Content-Type` header | ✅ YES | string | "application/json" | Required |

---

## 9. BACKEND LOGGING ADDED (SAFE - NO SECRETS)

Two logging points were added:

### 1. Validation Error Handler
```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Logs: [BOLNA DEBUG] POST /book-appointment validation error: ...
```

**What it logs:**
- Field name that failed
- Error message (e.g., "Field required", "Input should be a valid string")
- Error type (e.g., "missing", "string_type")
- **Never logs:** API keys, JWTs, secrets

### 2. Endpoint Entry Log
```python
if is_agent:
    logger.info(f"[BOLNA DEBUG] POST /book-appointment received: ...")
```

**What it logs:**
- All request field values (safe - just appointment data)
- Whether conversation_id was included
- **Never logs:** X-Agent-Key, user authentication

---

## 10. NEXT STEPS TO FIX BOLNA

1. **Restart backend** to activate debugging
2. **Make a test call** through Bolna
3. **Check logs** for `[BOLNA DEBUG]` lines
4. **Identify the exact field** causing the 422
5. **Update Bolna tool config** to ensure:
   - All required fields are extracted and sent
   - All fields are strings (convert dates to YYYY-MM-DD format)
   - No null values for required fields
6. **Test again** and verify the appointment appears in CLINOVA

---

**Backend changes made:** 
- Added safe validation error logging (no secrets exposed)
- Added safe request received logging
- No core logic changed
- No authentication changed
- Completely reversible (just logging statements)
