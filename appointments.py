from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, ensure_patient_access

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/patient/{patient_id}", response_model=schemas.AppointmentOut, status_code=201)
def create_appointment(
    patient_id: str,
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    doctor_id = payload.doctor_id
    if not doctor_id:
        patient = db.query(models.User).filter(models.User.id == patient_id).first()
        doctor_id = patient.assigned_doctor_id if patient else None

    appt = models.Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_at=payload.scheduled_at,
        reason=payload.reason,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.get("/patient/{patient_id}", response_model=list[schemas.AppointmentOut])
def list_appointments(
    patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_patient_access(patient_id, current_user, db)
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.patient_id == patient_id)
        .order_by(models.Appointment.scheduled_at.asc())
        .all()
    )


@router.patch("/{appointment_id}/status", response_model=schemas.AppointmentOut)
def update_appointment_status(
    appointment_id: str,
    status_value: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    ensure_patient_access(appt.patient_id, current_user, db)
    if status_value not in ("scheduled", "completed", "missed", "cancelled"):
        raise HTTPException(status_code=400, detail="Invalid status value")
    appt.status = status_value
    db.commit()
    db.refresh(appt)
    return appt
