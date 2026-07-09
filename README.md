# AI-Powered Post-Surgery Recovery & Intelligent Monitoring Assistant — Backend

FastAPI backend implementing every feature in the problem statement:

- AI-generated personalized recovery plans (from discharge summary text, via Claude)
- Computer-vision wound infection risk detection (Normal / Mild Concern / Urgent)
- Medication reminders + adherence tracking
- Rehabilitation exercise guidance
- Diet recommendations
- Daily health check-ins & symptom tracking
- Voice assistant (intent parsing from speech-to-text transcripts)
- Recovery progress dashboard data
- Smart alerts to caregivers & doctors
- Doctor dashboard (patient list, full reports, adherence, wound trend)
- Emergency SOS with location sharing
- JWT-secured, role-based (patient / doctor / caregiver / admin)

## 1. Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env:
#   - set ANTHROPIC_API_KEY to enable real AI discharge-summary parsing,
#     recovery plan generation, and voice NLU (falls back to rule-based
#     logic automatically if left blank, so the app still runs without it)
#   - set SECRET_KEY to a long random string for production
#   - optionally set Twilio/SendGrid credentials for real SMS/email alerts
```

## 2. Run

```bash
uvicorn app.main:app --reload --port 8000
```

API docs (Swagger UI): http://localhost:8000/docs
Alternative docs (ReDoc): http://localhost:8000/redoc

## 3. Seed demo data (optional)

```bash
python seed_demo_data.py
```

Creates:
- `doctor@demo.com` / `password123`
- `caregiver@demo.com` / `password123`
- `patient@demo.com` / `password123` (assigned to the demo doctor, linked to the demo caregiver)

## 4. Typical flow

1. `POST /auth/register` — create patient / doctor / caregiver accounts (patients can pass `assigned_doctor_id`)
2. `POST /auth/login` — OAuth2 password flow, returns a JWT `access_token`. Send it as `Authorization: Bearer <token>` on all other requests.
3. `POST /discharge-summaries/upload?patient_id=...` (multipart file) — AI extracts meds/rehab/diet/follow-ups and auto-generates the active `RecoveryPlan` + `Medication` records.
4. `GET /discharge-summaries/patient/{id}/active-plan` — fetch the generated plan.
5. `POST /wounds/patient/{id}/upload` (multipart image) — runs CV analysis, stores risk level, auto-raises an `Alert` + notifies caregivers/doctor if risk is Mild Concern or Urgent.
6. `POST /checkins/patient/{id}` — daily symptom/pain/temperature check-in; auto-flags and alerts on concerning values.
7. `POST /voice/query` — send a speech-to-text transcript (e.g. "I took my antibiotic"), get back an intent, any action taken, and a spoken-style reply.
8. `POST /sos/patient/{id}` — emergency SOS with optional lat/lng; immediately alerts doctor + caregivers.
9. `GET /doctor/patients` — doctor's dashboard list with latest check-in, wound risk, open alert count, adherence %.
10. `GET /doctor/patients/{id}/full-report` — full recovery history for one patient.

## 5. Architecture notes

```
app/
  main.py            FastAPI app, router registration, startup scheduler
  config.py          Settings (env vars)
  database.py        SQLAlchemy engine/session
  models.py           SQLAlchemy ORM models
  schemas.py          Pydantic request/response schemas
  auth.py              Password hashing + JWT
  dependencies.py     get_current_user, role guards, patient-access guard
  routers/
    auth.py            register/login/me/caregiver-links
    patients.py         patient profile, doctor listing
    discharge.py         discharge summary upload -> AI extraction -> recovery plan
    medications.py       med CRUD, adherence logs
    wounds.py             wound image upload -> CV analysis -> alerts
    checkins.py            daily check-ins -> risk evaluation -> alerts
    voice.py                voice assistant intent handling
    alerts.py                alert listing/status updates
    appointments.py           follow-up appointment scheduling
    sos.py                    emergency SOS
    doctor.py                  doctor dashboard + full patient report
  services/
    ai_service.py        Claude API wrapper: discharge parsing, plan
                          generation, voice NLU (graceful rule-based fallback)
    cv_service.py         Wound image risk classifier (heuristic; swap in a
                           trained CNN by replacing analyze_wound_image body)
    notification_service.py  Alert creation + SMS/email dispatch (Twilio/
                              SendGrid stubs — wire up your provider)
    scheduler.py           APScheduler background jobs: medication reminders,
                            missed-dose alerts, daily check-in reminders
```

### Swapping in a real wound-detection model
`app/services/cv_service.py` exposes one function, `analyze_wound_image(path) -> dict`,
with a fixed return schema. Replace its internals with inference calls to a
trained model (e.g. a fine-tuned CNN/ViT served via TorchServe, ONNX Runtime,
or a hosted endpoint) without touching any router code.

### Swapping in real OCR / PDF text extraction
`app/routers/discharge.py:_extract_text_from_upload` currently only reads
`.txt` files natively. Plug in `pytesseract` (for scanned images) or a PDF
text extractor (e.g. `pypdf`, `pdfplumber`) there to handle real discharge
PDFs/photos.

### Database
Defaults to SQLite for zero-config local development. Set `DATABASE_URL` in
`.env` to a Postgres URL for production (e.g.
`postgresql://user:pass@host:5432/dbname`) — no code changes required.

### Security notes for production
- Move `SECRET_KEY` to a secrets manager; never commit `.env`.
- Put uploaded files (discharge summaries, wound images) in encrypted
  object storage (S3 + KMS) instead of local disk — `UPLOAD_DIR` is a drop-in
  swap point.
- Add rate limiting on `/auth/login` and `/sos/*`.
- Add audit logging for PHI access per HIPAA/local health-data regulations.
