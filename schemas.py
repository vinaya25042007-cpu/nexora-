from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field
from app.models import UserRole, RiskLevel, AlertStatus


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6)
    role: UserRole = UserRole.PATIENT
    date_of_birth: Optional[str] = None
    assigned_doctor_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    assigned_doctor_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CaregiverLinkCreate(BaseModel):
    patient_id: str
    caregiver_email: EmailStr
    relationship_label: str = "family"


# ---------- Discharge Summary / Recovery Plan ----------

class DischargeSummaryOut(BaseModel):
    id: str
    patient_id: str
    file_path: str
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class RecoveryPlanOut(BaseModel):
    id: str
    patient_id: str
    discharge_summary_id: str
    summary_text: Optional[str] = None
    diet_recommendations: Optional[Any] = None
    rehab_plan: Optional[Any] = None
    follow_up_schedule: Optional[Any] = None
    precautions: Optional[Any] = None
    generated_at: datetime

    class Config:
        from_attributes = True


# ---------- Medications ----------

class MedicationOut(BaseModel):
    id: str
    name: str
    dosage: Optional[str]
    frequency_per_day: int
    times: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    instructions: Optional[str]
    active: bool

    class Config:
        from_attributes = True


class MedicationCreate(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency_per_day: int = 1
    times: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    instructions: Optional[str] = None


class MedicationLogUpdate(BaseModel):
    taken: bool
    skipped_reason: Optional[str] = None


class MedicationLogOut(BaseModel):
    id: str
    medication_id: str
    scheduled_time: datetime
    taken: bool
    taken_at: Optional[datetime]
    skipped_reason: Optional[str]

    class Config:
        from_attributes = True


# ---------- Wound Analysis ----------

class WoundAnalysisOut(BaseModel):
    id: str
    wound_image_id: str
    risk_level: RiskLevel
    redness_score: float
    swelling_score: float
    discharge_score: float
    confidence: float
    findings: Optional[Any] = None
    recommendation: Optional[str] = None
    analyzed_at: datetime

    class Config:
        from_attributes = True


class WoundImageOut(BaseModel):
    id: str
    patient_id: str
    file_path: str
    uploaded_at: datetime
    day_since_surgery: Optional[int] = None
    analysis: Optional[WoundAnalysisOut] = None

    class Config:
        from_attributes = True


# ---------- Check-ins ----------

class CheckInCreate(BaseModel):
    pain_level: Optional[int] = Field(default=None, ge=0, le=10)
    temperature_c: Optional[float] = None
    mobility_level: Optional[int] = Field(default=None, ge=0, le=5)
    mood: Optional[str] = None
    symptoms: Optional[List[str]] = None
    notes: Optional[str] = None
    source: str = "app"


class CheckInOut(BaseModel):
    id: str
    patient_id: str
    pain_level: Optional[int]
    temperature_c: Optional[float]
    mobility_level: Optional[int]
    mood: Optional[str]
    symptoms: Optional[Any] = None
    notes: Optional[str]
    source: str
    created_at: datetime
    flagged: bool

    class Config:
        from_attributes = True


# ---------- Voice Assistant ----------

class VoiceQuery(BaseModel):
    transcript: str


class VoiceResponse(BaseModel):
    reply_text: str
    intent: str
    action_taken: Optional[str] = None
    data: Optional[Any] = None


# ---------- Alerts ----------

class AlertOut(BaseModel):
    id: str
    patient_id: str
    source_type: str
    source_id: Optional[str]
    severity: RiskLevel
    message: str
    status: AlertStatus
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


# ---------- Appointments ----------

class AppointmentCreate(BaseModel):
    doctor_id: Optional[str] = None
    scheduled_at: datetime
    reason: Optional[str] = None


class AppointmentOut(BaseModel):
    id: str
    patient_id: str
    doctor_id: Optional[str]
    scheduled_at: datetime
    reason: Optional[str]
    status: str
    notes: Optional[str]

    class Config:
        from_attributes = True


# ---------- SOS ----------

class SOSCreate(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    message: Optional[str] = None


class SOSOut(BaseModel):
    id: str
    patient_id: str
    lat: Optional[float]
    lng: Optional[float]
    message: Optional[str]
    created_at: datetime
    resolved: bool

    class Config:
        from_attributes = True


# ---------- Doctor dashboard ----------

class PatientSummary(BaseModel):
    patient: UserOut
    latest_checkin: Optional[CheckInOut] = None
    latest_wound_risk: Optional[RiskLevel] = None
    open_alerts: int = 0
    medication_adherence_pct: Optional[float] = None
