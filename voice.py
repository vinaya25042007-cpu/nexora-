import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user
from app.services import ai_service
from app.services.notification_service import create_alert

router = APIRouter(prefix="/voice", tags=["Voice Assistant"])


@router.post("/query", response_model=schemas.VoiceResponse)
def voice_query(
    payload: schemas.VoiceQuery,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Hands-free voice endpoint. Client sends a speech-to-text transcript;
    this endpoint classifies intent, performs the action, and returns text
    for the client to speak back (via on-device text-to-speech)."""
    if current_user.role != models.UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Voice assistant is available to patients")

    parsed = ai_service.parse_voice_command(payload.transcript)
    intent = parsed.get("intent", "unclear")
    entities = parsed.get("entities", {})
    action_taken = None
    data = None

    if intent == "log_medication_taken":
        med_name = entities.get("medication_name")
        med_q = db.query(models.Medication).filter(
            models.Medication.patient_id == current_user.id, models.Medication.active == True  # noqa: E712
        )
        if med_name:
            med_q = med_q.filter(models.Medication.name.ilike(f"%{med_name}%"))
        med = med_q.first()
        if med:
            log = models.MedicationLog(
                medication_id=med.id,
                patient_id=current_user.id,
                scheduled_time=datetime.utcnow(),
                taken=True,
                taken_at=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
            action_taken = f"Logged {med.name} as taken"
        else:
            action_taken = "No matching active medication found"

    elif intent == "log_pain_level":
        pain = entities.get("pain_level")
        checkin = models.CheckIn(
            patient_id=current_user.id,
            pain_level=pain,
            symptoms=json.dumps([]),
            source="voice",
        )
        db.add(checkin)
        db.commit()
        action_taken = f"Logged pain level {pain}" if pain is not None else "Logged a general check-in"

    elif intent == "log_symptom":
        symptom = entities.get("symptom")
        checkin = models.CheckIn(
            patient_id=current_user.id,
            symptoms=json.dumps([symptom] if symptom else []),
            notes=payload.transcript,
            source="voice",
        )
        db.add(checkin)
        db.commit()
        action_taken = f"Logged symptom: {symptom}" if symptom else "Logged symptom note"

    elif intent == "ask_recovery_plan":
        plan = (
            db.query(models.RecoveryPlan)
            .filter(models.RecoveryPlan.patient_id == current_user.id, models.RecoveryPlan.is_active == True)  # noqa: E712
            .first()
        )
        data = {"summary_text": plan.summary_text} if plan else None
        action_taken = "Fetched recovery plan"

    elif intent == "ask_next_appointment":
        appt = (
            db.query(models.Appointment)
            .filter(
                models.Appointment.patient_id == current_user.id,
                models.Appointment.status == "scheduled",
                models.Appointment.scheduled_at >= datetime.utcnow(),
            )
            .order_by(models.Appointment.scheduled_at.asc())
            .first()
        )
        if appt:
            data = {"scheduled_at": appt.scheduled_at.isoformat(), "reason": appt.reason}
        action_taken = "Fetched next appointment"

    elif intent == "request_sos":
        sos = models.SOSEvent(patient_id=current_user.id, message=payload.transcript)
        db.add(sos)
        db.commit()
        db.refresh(sos)
        create_alert(
            db,
            current_user,
            source_type="sos",
            source_id=sos.id,
            severity=models.RiskLevel.URGENT,
            message=f"SOS triggered by voice command for {current_user.full_name}: '{payload.transcript}'",
        )
        action_taken = "SOS alert sent to caregivers and care team"

    return schemas.VoiceResponse(
        reply_text=parsed.get("reply_text", "Okay."),
        intent=intent,
        action_taken=action_taken,
        data=data,
    )
