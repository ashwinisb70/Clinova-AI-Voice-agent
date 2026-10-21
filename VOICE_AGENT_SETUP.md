# Clinova AI Voice Agent: Setup and Tool Configuration

This guide covers running Clinova locally and configuring the existing Bolna voice agent's custom tools to call the backend. Everything below uses placeholder values. Real keys belong only in your local `backend/.env` and in the Bolna dashboard.

## 1. Install

Backend (from `backend/`):

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # only needed to run the tests
```

Frontend (from `frontend/`):

```bash
npm install
cp .env.example .env                 # then set VITE_API_URL if the backend is not on localhost:8000
```

## 2. Environment variables (`backend/.env`)

Copy `backend/.env.example` to `backend/.env` and fill in your values.

| Variable | Required | Purpose |
|---|---|---|
| `MONGODB_URI`, `MONGODB_DB_NAME` | yes | Your MongoDB database (the system of record) |
| `JWT_SECRET` | yes | Signs staff and patient tokens. Use a long random value. |
| `DEFAULT_HOSPITAL_ID` | yes | Tenant used when a request has no `X-Hospital-Id` header |
| `AGENT_API_KEY` | yes for voice | Shared secret the voice agent sends as `X-Agent-Key`. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Without it every agent call returns 503. |
| `BOLNA_API_KEY`, `BOLNA_AGENT_ID`, `BOLNA_API_BASE` | only for callbacks | Used only by the "request a callback" feature. `BOLNA_API_BASE` defaults to `https://api.bolna.ai` in code. Confirm this matches your Bolna account. |
| `AI_RECEPTIONIST_PHONE` | optional | Number patients dial to reach the agent |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `EMAIL_FROM`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | optional | SMTP for appointment emails. If unset, emails are logged as `failed` in `email_logs` and bookings still succeed. |
| `ALLOWED_ORIGINS`, `FRONTEND_URL` | yes for the web app | CORS and links in emails |

## 3. Run locally

```bash
# backend/
uvicorn main:app --reload --port 8000

# frontend/
npm run dev        # http://localhost:5173
```

Bolna cannot reach `localhost`. To test the live agent, expose the backend over HTTPS with a tunnel of your choice (for example ngrok or cloudflared) and use that URL as the base for the tools below.

## 4. Bolna custom tools

The tool definitions live in the Bolna dashboard, not in this repository. Create or update these four tools so they match the backend exactly.

**Headers on every tool:**

```
Content-Type: application/json
X-Agent-Key: <AGENT_API_KEY>
X-Hospital-Id: <hospital id, e.g. DEFAULT>
X-Conversation-Id: <Bolna call/execution id>     (recommended on the booking tool)
```

| Tool name | Method and path | Body fields | Required |
|---|---|---|---|
| `book_clinova_appointment` | `POST {BASE}/book-appointment` | `patient_name` (string), `department` (string), `preferred_date` (`YYYY-MM-DD`), `preferred_time` (e.g. `10:30 AM`), `doctor_id`, `notes` | `patient_name`, `department`, `preferred_date` |
| `check_appointment_status` | `POST {BASE}/agent/appointments/status` | `appointment_id`, `phone` | both |
| `reschedule_appointment` | `POST {BASE}/agent/appointments/reschedule` | `appointment_id`, `phone`, `preferred_date` (`YYYY-MM-DD`), `preferred_time` | all four |
| `cancel_appointment` | `POST {BASE}/agent/appointments/cancel` | `appointment_id`, `phone`, `confirmed` (boolean), `reason` (optional) | `appointment_id`, `phone` (`confirmed` defaults to false) |

Notes on the contract:

- **Booking** (`/book-appointment`) returns `appointment_id`, `status` and `message`. It is persisted before the response is sent. Its `status` is `pending` until hospital staff confirm it, so the agent should describe it as a request that has been recorded and is awaiting confirmation. Confirm this wording with the hospital; it is a business rule, not a technical one.
- **Reschedule and cancel** verify the caller. The `phone` must match the phone number on the patient account that owns the appointment (the last 10 digits are compared). Only appointments linked to a patient account can be changed by voice. Appointments created through the voice agent without a patient account return `409`.
- **Cancel** must be called first with `confirmed: false` to get the confirmation prompt, and again with `confirmed: true` only after the caller says yes.
- **Response handling for the agent prompt:**
  - `200` means the change is saved. Read `message` or the returned details. Never say success without a `200`.
  - `404` or `409` or `422` means nothing changed. Read `detail` to the caller. Its text is written for callers.
  - `503` means the database could not confirm the operation. Tell the caller that the change could not be confirmed and to check again shortly. Do not say it succeeded.
  - Retries with the same `X-Conversation-Id` do not create duplicate bookings, and repeated reschedule or cancel calls do not send duplicate notifications.

## 5. Email and SMS

- **Email** is optional. It is sent only to the email address on the verified patient record, and only after the database write succeeds. Voice bookings with no registered patient never receive email, even if the caller supplies an address. Delivery happens in the background. A failure is recorded in `email_logs` and never changes the booking result.
- **SMS** is not implemented in this codebase. No SMS provider integration exists, so none is claimed. To add one, choose a provider, add a module under `backend/services/`, store its credentials in `.env`, and send only after a documented consent check against the verified phone number.

## 6. Manual steps that remain

These cannot be verified from source code:

1. Create or update the four Bolna tools above, and confirm the base URL is reachable over HTTPS from Bolna.
2. Set the Bolna agent prompt so it follows the response rules in section 4.
3. Run one live test call end to end (booking, status, reschedule, cancel) using a test patient account. This uses the paid provider and was not run here.
4. Set SMTP values and confirm a test email arrives in a real inbox.
5. Confirm `BOLNA_API_BASE` for your account.

## 7. Automated tests

```bash
# backend/
python -m pytest -q
# frontend/
npm run build
```

The suite uses an in-memory MongoDB, mocked notification and email stores, and no external services. It never places voice calls and never sends real email. See `CHANGES_AND_VERIFICATION.md` for the latest results.
