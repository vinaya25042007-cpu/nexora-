from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import decode_access_token
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: models.UserRole):
    def checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in roles]}",
            )
        return current_user

    return checker


def ensure_patient_access(patient_id: str, current_user: models.User, db) -> None:
    """Raise 403 unless current_user is the patient themself, their assigned doctor,
    a linked caregiver, or an admin."""
    if current_user.role == models.UserRole.ADMIN:
        return
    if current_user.id == patient_id:
        return
    if current_user.role == models.UserRole.DOCTOR:
        patient = db.query(models.User).filter(models.User.id == patient_id).first()
        if patient and patient.assigned_doctor_id == current_user.id:
            return
    if current_user.role == models.UserRole.CAREGIVER:
        link = (
            db.query(models.CaregiverLink)
            .filter(
                models.CaregiverLink.patient_id == patient_id,
                models.CaregiverLink.caregiver_id == current_user.id,
            )
            .first()
        )
        if link:
            return
    from fastapi import HTTPException, status

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this patient")
