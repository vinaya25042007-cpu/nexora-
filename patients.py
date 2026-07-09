from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, ensure_patient_access

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/{patient_id}", response_model=schemas.UserOut)
def get_patient_profile(
    patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_patient_access(patient_id, current_user, db)
    patient = db.query(models.User).filter(
        models.User.id == patient_id, models.User.role == models.UserRole.PATIENT
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/", response_model=list[schemas.UserOut])
def list_doctors(db: Session = Depends(get_db)):
    """Public-ish listing of doctors so patients can choose one at signup.
    (In production, gate this behind auth / an org directory as needed.)"""
    return db.query(models.User).filter(models.User.role == models.UserRole.DOCTOR).all()


@router.patch("/{patient_id}/assigned-doctor")
def set_assigned_doctor(
    patient_id: str,
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    doctor = db.query(models.User).filter(
        models.User.id == doctor_id, models.User.role == models.UserRole.DOCTOR
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    patient = db.query(models.User).filter(models.User.id == patient_id).first()
    patient.assigned_doctor_id = doctor_id
    db.commit()
    return {"patient_id": patient_id, "assigned_doctor_id": doctor_id}
