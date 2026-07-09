from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, ensure_patient_access

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.get("/patient/{patient_id}", response_model=list[schemas.MedicationOut])
def list_medications(
    patient_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    q = db.query(models.Medication).filter(models.Medication.patient_id == patient_id)
    if active_only:
        q = q.filter(models.Medication.active == True)  # noqa: E712
    return q.all()


@router.post("/patient/{patient_id}", response_model=schemas.MedicationOut, status_code=201)
def add_medication(
    patient_id: str,
    payload: schemas.MedicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Doctors (or the patient) can manually add/adjust a medication."""
    ensure_patient_access(patient_id, current_user, db)
    plan = (
        db.query(models.RecoveryPlan)
        .filter(models.RecoveryPlan.patient_id == patient_id, models.RecoveryPlan.is_active == True)  # noqa: E712
        .first()
    )
    if not plan:
        raise HTTPException(status_code=400, detail="Patient has no active recovery plan to attach medication to")

    med = models.Medication(recovery_plan_id=plan.id, patient_id=patient_id, **payload.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


@router.patch("/{medication_id}/deactivate", response_model=schemas.MedicationOut)
def deactivate_medication(
    medication_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    med = db.query(models.Medication).filter(models.Medication.id == medication_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    ensure_patient_access(med.patient_id, current_user, db)
    med.active = False
    db.commit()
    db.refresh(med)
    return med


@router.get("/patient/{patient_id}/logs", response_model=list[schemas.MedicationLogOut])
def list_medication_logs(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    return (
        db.query(models.MedicationLog)
        .filter(models.MedicationLog.patient_id == patient_id)
        .order_by(models.MedicationLog.scheduled_time.desc())
        .limit(200)
        .all()
    )


@router.post("/logs/{log_id}/mark", response_model=schemas.MedicationLogOut)
def mark_medication_log(
    log_id: str,
    payload: schemas.MedicationLogUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    log = db.query(models.MedicationLog).filter(models.MedicationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Medication log not found")
    ensure_patient_access(log.patient_id, current_user, db)

    log.taken = payload.taken
    log.skipped_reason = payload.skipped_reason
    log.taken_at = datetime.utcnow() if payload.taken else None
    db.commit()
    db.refresh(log)
    return log


@router.get("/patient/{patient_id}/adherence")
def get_adherence(
    patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_patient_access(patient_id, current_user, db)
    logs = db.query(models.MedicationLog).filter(models.MedicationLog.patient_id == patient_id).all()
    if not logs:
        return {"adherence_pct": None, "total_scheduled": 0, "total_taken": 0}
    taken = sum(1 for lg in logs if lg.taken)
    return {
        "adherence_pct": round(100.0 * taken / len(logs), 1),
        "total_scheduled": len(logs),
        "total_taken": taken,
    }
