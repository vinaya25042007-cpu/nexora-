import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    CAREGIVER = "caregiver"
    ADMIN = "admin"


class RiskLevel(str, enum.Enum):
    NORMAL = "normal"
    MILD_CONCERN = "mild_concern"
    URGENT = "urgent"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.PATIENT)
    date_of_birth = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # patient-specific
    assigned_doctor_id = Column(String, ForeignKey("users.id"), nullable=True)
    last_known_lat = Column(Float, nullable=True)
    last_known_lng = Column(Float, nullable=True)

    discharge_summaries = relationship(
        "DischargeSummary", back_populates="patient",
        foreign_keys="DischargeSummary.patient_id"
    )


class CaregiverLink(Base):
    """Links a caregiver to a patient (many caregivers can watch one patient)."""
    __tablename__ = "caregiver_links"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    caregiver_id = Column(String, ForeignKey("users.id"), nullable=False)
    relationship_label = Column(String, default="family")
    notify_sms = Column(Boolean, default=True)
    notify_email = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DischargeSummary(Base):
    __tablename__ = "discharge_summaries"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    surgery_type = Column(String, nullable=True)
    surgery_date = Column(String, nullable=True)
    ai_extracted_json = Column(Text, nullable=True)  # structured JSON from AI
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("User", back_populates="discharge_summaries", foreign_keys=[patient_id])
    recovery_plan = relationship("RecoveryPlan", back_populates="discharge_summary", uselist=False)


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    discharge_summary_id = Column(String, ForeignKey("discharge_summaries.id"), nullable=False)
    summary_text = Column(Text, nullable=True)
    diet_recommendations = Column(Text, nullable=True)   # JSON list
    rehab_plan = Column(Text, nullable=True)              # JSON list of exercises
    follow_up_schedule = Column(Text, nullable=True)      # JSON list of dates/notes
    precautions = Column(Text, nullable=True)             # JSON list
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    discharge_summary = relationship("DischargeSummary", back_populates="recovery_plan")
    medications = relationship("Medication", back_populates="recovery_plan")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(String, primary_key=True, default=gen_uuid)
    recovery_plan_id = Column(String, ForeignKey("recovery_plans.id"), nullable=False)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    frequency_per_day = Column(Integer, default=1)
    times = Column(String, nullable=True)  # comma-separated "08:00,14:00,20:00"
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    active = Column(Boolean, default=True)

    recovery_plan = relationship("RecoveryPlan", back_populates="medications")
    logs = relationship("MedicationLog", back_populates="medication")


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    medication_id = Column(String, ForeignKey("medications.id"), nullable=False)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    taken = Column(Boolean, default=False)
    taken_at = Column(DateTime, nullable=True)
    skipped_reason = Column(String, nullable=True)

    medication = relationship("Medication", back_populates="logs")


class WoundImage(Base):
    __tablename__ = "wound_images"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    day_since_surgery = Column(Integer, nullable=True)

    analysis = relationship("WoundAnalysis", back_populates="wound_image", uselist=False)


class WoundAnalysis(Base):
    __tablename__ = "wound_analyses"

    id = Column(String, primary_key=True, default=gen_uuid)
    wound_image_id = Column(String, ForeignKey("wound_images.id"), nullable=False)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    redness_score = Column(Float, default=0.0)
    swelling_score = Column(Float, default=0.0)
    discharge_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    findings = Column(Text, nullable=True)  # JSON list of textual findings
    recommendation = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    wound_image = relationship("WoundImage", back_populates="analysis")


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    pain_level = Column(Integer, nullable=True)       # 0-10
    temperature_c = Column(Float, nullable=True)
    mobility_level = Column(Integer, nullable=True)   # 0-5
    mood = Column(String, nullable=True)
    symptoms = Column(Text, nullable=True)            # JSON list of symptom strings
    notes = Column(Text, nullable=True)
    source = Column(String, default="app")            # app | voice
    created_at = Column(DateTime, default=datetime.utcnow)
    flagged = Column(Boolean, default=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(String, ForeignKey("users.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="scheduled")  # scheduled|completed|missed|cancelled
    notes = Column(Text, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    source_type = Column(String, nullable=False)  # wound_analysis|checkin|sos|medication
    source_id = Column(String, nullable=True)
    severity = Column(Enum(RiskLevel), default=RiskLevel.MILD_CONCERN)
    message = Column(Text, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class SOSEvent(Base):
    __tablename__ = "sos_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
