import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, require_role, ensure_patient_access

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])


@router.get("/patients", response_model=list[schemas.PatientSummary])
def list_my_patients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.DOCTOR, models.UserRole.ADMIN)),
):
    q = db.query(models.User).filter(models.User.role == models.UserRole.PATIENT)
    if current_user.role == models.UserRole.DOCTOR:
        q = q.filter(models.User.assigned_doctor_id == current_user.id)
    patients = q.all()

    summaries = []
    for patient in patients:
        latest_checkin = (
            db.query(models.CheckIn)
            .filter(models.CheckIn.patient_id == patient.id)
            .order_by(models.CheckIn.created_at.desc())
            .first()
        )
        latest_wound = (
            db.query(models.WoundAnalysis)
            .filter(models.WoundAnalysis.patient_id == patient.id)
            .order_by(models.WoundAnalysis.analyzed_at.desc())
            .first()
        )
        open_alerts = (
            db.query(models.Alert)
            .filter(models.Alert.patient_id == patient.id, models.Alert.status == models.AlertStatus.OPEN)
            .count()
        )
        logs = db.query(models.MedicationLog).filter(models.MedicationLog.patient_id == patient.id).all()
        adherence = None
        if logs:
            taken = sum(1 for lg in logs if lg.taken)
            adherence = round(100.0 * taken / len(logs), 1)

        checkin_out = None
        if latest_checkin:
            checkin_out = schemas.CheckInOut.model_validate(latest_checkin)
            checkin_out.symptoms = json.loads(latest_checkin.symptoms or "[]")

        summaries.append(
            schemas.PatientSummary(
                patient=schemas.UserOut.model_validate(patient),
                latest_checkin=checkin_out,
                latest_wound_risk=latest_wound.risk_level if latest_wound else None,
                open_alerts=open_alerts,
                medication_adherence_pct=adherence,
            )
        )
    return summaries


@router.get("/patients/{patient_id}/full-report")
def patient_full_report(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.DOCTOR, models.UserRole.ADMIN)),
):
    """Comprehensive report: recovery plan, wound progression, check-in trend,
    adherence, and alert history — everything a doctor needs in one view."""
    ensure_patient_access(patient_id, current_user, db)
    patient = db.query(models.User).filter(models.User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    plan = (
        db.query(models.RecoveryPlan)
        .filter(models.RecoveryPlan.patient_id == patient_id, models.RecoveryPlan.is_active == True)  # noqa: E712
        .first()
    )
    wound_history = (
        db.query(models.WoundAnalysis)
        .filter(models.WoundAnalysis.patient_id == patient_id)
        .order_by(models.WoundAnalysis.analyzed_at.asc())
        .all()
    )
    checkins = (
        db.query(models.CheckIn)
        .filter(models.CheckIn.patient_id == patient_id)
        .order_by(models.CheckIn.created_at.asc())
        .all()
    )
    logs = db.query(models.MedicationLog).filter(models.MedicationLog.patient_id == patient_id).all()
    alerts = (
        db.query(models.Alert)
        .filter(models.Alert.patient_id == patient_id)
        .order_by(models.Alert.created_at.desc())
        .all()
    )

    adherence_pct = None
    if logs:
        adherence_pct = round(100.0 * sum(1 for lg in logs if lg.taken) / len(logs), 1)

    return {
        "patient": schemas.UserOut.model_validate(patient),
        "recovery_plan_summary": plan.summary_text if plan else None,
        "wound_risk_trend": [
            {"date": w.analyzed_at.isoformat(), "risk_level": w.risk_level.value} for w in wound_history
        ],
        "pain_trend": [
            {"date": c.created_at.isoformat(), "pain_level": c.pain_level} for c in checkins if c.pain_level is not None
        ],
        "medication_adherence_pct": adherence_pct,
        "recent_alerts": [
            {
                "date": a.created_at.isoformat(),
                "severity": a.severity.value,
                "message": a.message,
                "status": a.status.value,
            }
            for a in alerts[:20]
        ],
    }
