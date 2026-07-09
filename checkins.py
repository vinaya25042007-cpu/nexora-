import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, ensure_patient_access
from app.services.notification_service import create_alert

router = APIRouter(prefix="/checkins", tags=["Health Check-ins"])

HIGH_PAIN_THRESHOLD = 7
FEVER_THRESHOLD_C = 38.0
CONCERNING_SYMPTOMS = {"fever", "chills", "severe pain", "shortness of breath", "chest pain", "confusion"}


def _evaluate_checkin_risk(checkin: models.CheckIn) -> tuple[bool, str | None]:
    reasons = []
    if checkin.pain_level is not None and checkin.pain_level >= HIGH_PAIN_THRESHOLD:
        reasons.append(f"high pain level ({checkin.pain_level}/10)")
    if checkin.temperature_c is not None and checkin.temperature_c >= FEVER_THRESHOLD_C:
        reasons.append(f"fever ({checkin.temperature_c}°C)")
    if checkin.symptoms:
        symptoms = json.loads(checkin.symptoms) if isinstance(checkin.symptoms, str) else checkin.symptoms
        matched = [s for s in symptoms if s.lower() in CONCERNING_SYMPTOMS]
        if matched:
            reasons.append(f"concerning symptoms: {', '.join(matched)}")
    if reasons:
        return True, "; ".join(reasons)
    return False, None


@router.post("/patient/{patient_id}", response_model=schemas.CheckInOut, status_code=201)
def create_checkin(
    patient_id: str,
    payload: schemas.CheckInCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    patient = db.query(models.User).filter(models.User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    checkin = models.CheckIn(
        patient_id=patient_id,
        pain_level=payload.pain_level,
        temperature_c=payload.temperature_c,
        mobility_level=payload.mobility_level,
        mood=payload.mood,
        symptoms=json.dumps(payload.symptoms or []),
        notes=payload.notes,
        source=payload.source,
    )

    flagged, reason = _evaluate_checkin_risk(checkin)
    checkin.flagged = flagged

    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    if flagged:
        severity = models.RiskLevel.URGENT if (
            payload.temperature_c and payload.temperature_c >= 39.0
        ) or (payload.pain_level and payload.pain_level >= 9) else models.RiskLevel.MILD_CONCERN

        create_alert(
            db,
            patient,
            source_type="checkin",
            source_id=checkin.id,
            severity=severity,
            message=f"{patient.full_name}'s check-in flagged a concern: {reason}",
        )

    out = schemas.CheckInOut.model_validate(checkin)
    out.symptoms = payload.symptoms or []
    return out


@router.get("/patient/{patient_id}", response_model=list[schemas.CheckInOut])
def list_checkins(
    patient_id: str,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    checkins = (
        db.query(models.CheckIn)
        .filter(models.CheckIn.patient_id == patient_id)
        .order_by(models.CheckIn.created_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for c in checkins:
        out = schemas.CheckInOut.model_validate(c)
        out.symptoms = json.loads(c.symptoms or "[]")
        results.append(out)
    return results
