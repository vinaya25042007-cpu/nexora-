from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, ensure_patient_access

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/patient/{patient_id}", response_model=list[schemas.AlertOut])
def list_alerts(
    patient_id: str,
    status_filter: models.AlertStatus | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    q = db.query(models.Alert).filter(models.Alert.patient_id == patient_id)
    if status_filter:
        q = q.filter(models.Alert.status == status_filter)
    return q.order_by(models.Alert.created_at.desc()).all()


@router.patch("/{alert_id}/status", response_model=schemas.AlertOut)
def update_alert_status(
    alert_id: str,
    payload: schemas.AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    ensure_patient_access(alert.patient_id, current_user, db)

    if current_user.role == models.UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only doctors, caregivers, or admins can update alert status")

    alert.status = payload.status
    if payload.status == models.AlertStatus.RESOLVED:
        alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
