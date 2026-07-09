from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401  (ensures models are registered before create_all)
from app.services.scheduler import start_scheduler

from app.routers import (
    auth,
    patients,
    discharge,
    medications,
    wounds,
    checkins,
    voice,
    alerts,
    appointments,
    sos,
    doctor,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Post-Surgery Recovery & Intelligent Monitoring Assistant",
    description=(
        "Backend API for personalized recovery plans, wound-image infection risk "
        "detection, medication adherence, symptom check-ins, voice assistant, "
        "smart alerts, and doctor/caregiver monitoring dashboards."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(discharge.router)
app.include_router(medications.router)
app.include_router(wounds.router)
app.include_router(checkins.router)
app.include_router(voice.router)
app.include_router(alerts.router)
app.include_router(appointments.router)
app.include_router(sos.router)
app.include_router(doctor.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "recovery-assistant-backend"}
