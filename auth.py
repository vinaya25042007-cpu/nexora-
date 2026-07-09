from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.assigned_doctor_id:
        doctor = db.query(models.User).filter(
            models.User.id == payload.assigned_doctor_id, models.User.role == models.UserRole.DOCTOR
        ).first()
        if not doctor:
            raise HTTPException(status_code=400, detail="assigned_doctor_id does not refer to a valid doctor")

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        date_of_birth=payload.date_of_birth,
        assigned_doctor_id=payload.assigned_doctor_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/caregiver-links", status_code=status.HTTP_201_CREATED)
def link_caregiver(
    payload: schemas.CaregiverLinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Link an existing caregiver account to a patient. Callable by the patient themself
    (linking their own caregiver) or an admin."""
    if current_user.role not in (models.UserRole.PATIENT, models.UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only patients or admins can create caregiver links")
    if current_user.role == models.UserRole.PATIENT and current_user.id != payload.patient_id:
        raise HTTPException(status_code=403, detail="Patients may only link caregivers to themselves")

    caregiver = db.query(models.User).filter(
        models.User.email == payload.caregiver_email, models.User.role == models.UserRole.CAREGIVER
    ).first()
    if not caregiver:
        raise HTTPException(status_code=404, detail="No caregiver account found with that email")

    link = models.CaregiverLink(
        patient_id=payload.patient_id,
        caregiver_id=caregiver.id,
        relationship_label=payload.relationship_label,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return {"id": link.id, "patient_id": link.patient_id, "caregiver_id": link.caregiver_id}
