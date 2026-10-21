# Clinova: Changes and Verification Record

This records what was inspected, what was changed, how it was tested, and what is still unverified. The frontend UI was not modified. The original ZIP was not modified.

## 1. Findings from inspection

| # | Finding | Where | Status |
|---|---|---|---|
| 1 | Notifications, email, invoice creation and activity logging ran after the appointment was saved, with no error handling. A failure there returned a 500 for a booking that was actually saved, which invites a duplicate retry. | `services/booking.py`, `services/notify.py`, `services/appointment_ops.py`, `main.py` | Fixed |
| 2 | Voice bookings emailed the address the caller supplied, which is unverified. | `services/booking.py` | Fixed. Email now goes only to the verified patient record. |
| 3 | `email_queued` was reported `true` for caller-supplied addresses that were never emailed. | `main.py` | Fixed |
| 4 | "Today" was computed with the server clock (UTC). For IST callers between 00:00 and 05:30 IST, same-day bookings were rejected. | `services/booking.py`, `services/appointment_ops.py`, `routers/extended_appointments.py` | Fixed with `today_local()` (Asia/Kolkata) |
| 5 | Voice booking logs printed patient name, email and notes. Call logs stored the patient email. | `main.py` | Fixed. Logs now record only operational fields. Call logs store the email as `provided`. |
| 6 | Voice endpoints filtered by `hospital_id` directly instead of the shared tenant scope used elsewhere. Database errors returned generic 500 responses. | `routers/agent_appointments.py` | Fixed. Tenant scope is used, and database failures return 503 with an honest message. |
| 7 | Voice booking DB failures returned 500, and the agent had no accurate message to read. | `main.py` | Fixed. Returns 503 and states nothing was booked. |
| 8 | `pytz` is imported at runtime but missing from `requirements.txt`. Test dependencies were undocumented. Baseline tests failed to collect without `aiosmtpd`. | `requirements.txt`, new `requirements-dev.txt` | Fixed |
| 9 | `reset_password.py` contained a hard-coded account name and password. | `reset_password.py` | Fixed. Prompts for username and password. |
| 10 | `.env.example` set `BOLNA_API_BASE=https://api.bolna.dev`, but the code default is `https://api.bolna.ai`. | `backend/.env.example` | Aligned to the code default. Confirm against your Bolna account (unverified). |
| 11 | Voice cancellation wording did not match the agreed confirmation. | `routers/agent_appointments.py` | Now "Your appointment has been cancelled successfully." |
| 12 | Dashboard metrics were already implemented: Asia/Kolkata dates, completion timestamps, cleared on reopen. | `routers/admin.py`, `routers/appointments.py` | Verified by tests. No change needed. |

## 2. Files changed

| File | Change |
|---|---|
| `backend/services/common.py` | Added `LOCAL_TZ` (Asia/Kolkata) and `today_local()`. |
| `backend/services/notify.py` | `create_notification` and `email_patient` are best-effort: failures are logged and never raised. |
| `backend/services/booking.py` | Uses `today_local()`. Email only to the verified patient. Invoice creation is guarded after the insert. |
| `backend/services/appointment_ops.py` | Reschedule uses `today_local()`. Invoice update during cancel is guarded after the write. |
| `backend/routers/agent_appointments.py` | Rewritten: tenant scope, 503 on database failure, re-reads stored state before confirming, guarded activity logging, cancel message wording. Request and response shapes are unchanged. |
| `backend/routers/extended_appointments.py` | Recurring and walk-in dates use `today_local()`. |
| `backend/main.py` | Booking: database failure returns 503, PHI removed from logs, accurate `email_queued`, guarded activity logging, call logs do not store the email. |
| `backend/reset_password.py` | Prompts for username and password instead of hard-coding them. |
| `backend/requirements.txt` | Added `pytz`. |
| `backend/requirements-dev.txt` | New. Test dependencies. |
| `backend/.env.example` | `BOLNA_API_BASE` aligned to the code default. |
| `backend/tests/test_voice_reliability.py` | New. 19 focused tests (see section 3). |
| `VOICE_AGENT_SETUP.md` | New. Setup, environment, Bolna tool configuration, manual steps. |
| `CHANGES_AND_VERIFICATION.md` | New. This file. |

**Unchanged:** all of `frontend/`, all existing routes and their request and response fields, database schemas and collection names, authentication, the existing test files.

## 3. Test commands and actual results

Environment: Python 3.13.16, Node with `npm ci` from the lockfile.

| Command | Result |
|---|---|
| Baseline, unmodified copy: `cd backend && python -m pytest -q` (before `aiosmtpd` was installed) | Collection error: `ModuleNotFoundError: No module named 'aiosmtpd'` |
| Baseline, unmodified copy, after installing `aiosmtpd` | **85 passed** |
| New tests against **original** code: `pytest tests/test_voice_reliability.py` | **9 failed, 10 passed.** The 9 failures cover section 1 items 1, 2, 4, 6, 7 and 11. The 10 passing tests check behavior that already worked, and guard against regressions. |
| After changes: `cd backend && python -m pytest -q -p no:cacheprovider -W ignore` | **104 passed** |
| Voice and status subset: `pytest tests/test_voice_reliability.py tests/test_voice_appointments.py tests/test_voice_verification.py tests/test_appointment_status.py -q` | **66 passed** |
| Static check: `pyflakes` on changed backend files | Only pre-existing unused imports remain. No new warnings. |
| Frontend: `cd frontend && npm run build` (`tsc && vite build`) | **Exit 0.** Built in about 6 seconds. Chunk-size warning is pre-existing. |

### Voice-agent workflows and their test coverage

| Requirement | Automated coverage | Status |
|---|---|---|
| A. Book: persists, returns the real ID, rejects invalid input without creating records | `test_booking_persists_and_is_listed_for_staff`, `test_validation_failures_create_no_records`, `test_booking_date_validation_uses_kolkata_today` | Verified by tests |
| A. Book: database failure not reported as booked | `test_voice_booking_database_failure_is_not_reported_as_booked` | Verified by tests |
| A. Book: duplicate retries do not create duplicate bookings | Existing: `test_voice_retry_with_same_conversation_does_not_duplicate` | Verified by tests (existing suite) |
| B. Reschedule: persists the new date and time, returns accurate errors, nothing changes on conflict | `test_voice_reschedule_persists_new_date_and_time`, `test_voice_reschedule_into_taken_doctor_slot_returns_accurate_error` | Verified by tests |
| B. Reschedule: notification after success | Notification code path exists. Failure isolation is tested on cancel; a reschedule-specific notification assertion was not added. | Partially verified |
| C. Cancel: persists status, confirmation-first flow | `test_voice_cancel_persists_status_and_lookup_reflects_it`, `test_cancel_succeeds_when_notification_store_fails`, existing cancel tests | Verified by tests |
| D. Status lookup returns current database state | `test_status_lookup_returns_current_database_state` | Verified by tests |
| E. Backend and database errors returned accurately | `test_voice_lookup_database_failure_is_reported_as_unconfirmed`, `test_voice_booking_database_failure_is_not_reported_as_booked` | Verified by tests |
| E. Conversation quality: natural speech, asking follow-up questions, following the response rules | Not testable from this repository | **Requires live provider test** |

### Required test list (from the brief)

| # | Requirement | Covered by |
|---|---|---|
| 1 | Successful booking persists | `test_booking_persists_and_is_listed_for_staff` |
| 2 | Validation failures create no invalid records | `test_validation_failures_create_no_records` |
| 3 | Reschedule persists correct date and time | `test_voice_reschedule_persists_new_date_and_time` |
| 4 | Cancellation persists correct status | `test_voice_cancel_persists_status_and_lookup_reflects_it` |
| 5 | Status lookup returns current database state | `test_status_lookup_returns_current_database_state` |
| 6 | Completion timestamps and dates use Asia/Kolkata | `test_completion_date_uses_asia_kolkata_not_utc` |
| 7 | Reopening clears stale completion metadata | `test_reopening_completed_appointment_clears_completion_metadata` |
| 8 | Dashboard metrics count the correct appointments | `test_dashboard_counts_follow_records_and_exclude_cancelled` |
| 9 | Missing email does not prevent booking | `test_missing_email_does_not_block_voice_booking_and_unverified_address_gets_no_mail` |
| 10 | Notification failure does not falsely report a failed booking | `test_notification_store_failure_does_not_fail_saved_booking`, `test_email_queue_failure_does_not_fail_saved_booking` |
| 11 | Backend errors returned accurately to the voice agent | `test_voice_lookup_database_failure_is_reported_as_unconfirmed`, `test_voice_reschedule_into_taken_doctor_slot_returns_accurate_error` |
| 12 | Authentication and hospital isolation intact | `test_other_hospital_cannot_see_or_change_voice_booking`, `test_dashboard_is_scoped_to_hospital`, existing isolation tests |

Every test uses in-memory MongoDB (`mongomock://`) with an isolated tenant (`RELTEST`). SMTP is pointed at `127.0.0.1:8025`, where nothing listens, so background send attempts fail locally and are recorded as `failed` in the in-memory email log. No mail leaves the machine, no voice call is placed, and no real notification is made.

## 4. Email and SMS status

- **Email:** SMTP sending is implemented. Tests mock the database layer and do not deliver mail. Delivery to a real inbox was **not verified**. The SMTP configuration in `VOICE_AGENT_SETUP.md` must be set up and tested.
- **SMS:** **Not implemented.** The project has no SMS provider. Nothing has been claimed or added.

## 5. Known limitations and unverified items

1. **Live voice provider not tested.** Bolna tool definitions live in the Bolna dashboard. They were documented from the FastAPI implementation, not configured in Bolna. No paid call was placed.
2. **Conversation behaviour not testable here.** Whether the agent asks the right questions and follows the success and failure wording depends on the agent prompt.
3. **Booking status wording.** Voice bookings are saved as `pending` until staff confirm. The agent should describe them as recorded and awaiting confirmation. The brief's example said "successfully booked", which is a business decision for the hospital to confirm.
4. **Concurrent double booking.** The doctor-slot check runs before the insert, with no unique index. Two simultaneous requests for the same slot could both pass. A unique partial index would prevent this, but it could fail on existing data, so it was not added. Flagged for a planned migration.
5. **Email delivery in production** depends on the SMTP provider. Failures are recorded in `email_logs`, and staff can retry from the existing email screen.
6. **Frontend fallback.** `Dashboard.tsx` falls back to `completed_appointments` when `completed_today` is missing. The backend always returns the field, so the fallback is not reached. Left unchanged to preserve the frontend.
7. **`/dashboard/summary`** (`main.py`) counts all call logs, which have no hospital field. The admin dashboard uses `/admin/summary`, which is correctly scoped. Left unchanged.
8. **Historical data** was not backfilled. Old completed appointments without `completed_date` are not counted as completed today, per the brief.

## 6. Running the updated project

See `VOICE_AGENT_SETUP.md` for full steps. In short:

```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
cd frontend && npm install && npm run dev
cd backend && pip install -r requirements-dev.txt && python -m pytest -q
```
