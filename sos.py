from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.dependencies import get_current_user, ensure_patient_access
from app.services.notification_service import create_alert

router = APIRouter(prefix="/sos", tags=["Emergency SOS"])


@router.post("/patient/{patient_id}", response_model=schemas.SOSOut, status_code=201)
def trigger_sos(
    patient_id: str,
    payload: schemas.SOSCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    patient = db.query(models.User).filter(models.User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if payload.lat is not None and payload.lng is not None:
        patient.last_known_lat = payload.lat
        patient.last_known_lng = payload.lng

    sos = models.SOSEvent(
        patient_id=patient_id, lat=payload.lat, lng=payload.lng, message=payload.message
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)

    location_str = f" Location: ({payload.lat}, {payload.lng})." if payload.lat else ""
    create_alert(
        db,
        patient,
        source_type="sos",
        source_id=sos.id,
        severity=models.RiskLevel.URGENT,
        message=f"🆘 SOS triggered by {patient.full_name}.{location_str} {payload.message or ''}".strip(),
    )
    return sos


@router.patch("/{sos_id}/resolve", response_model=schemas.SOSOut)
def resolve_sos(
    sos_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    sos = db.query(models.SOSEvent).filter(models.SOSEvent.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS event not found")
    ensure_patient_access(sos.patient_id, current_user, db)
    sos.resolved = True
    db.commit()
    db.refresh(sos)
    return sos


@router.get("/patient/{patient_id}", response_model=list[schemas.SOSOut])
def list_sos_events(
    patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_patient_access(patient_id, current_user, db)
    return (
        db.query(models.SOSEvent)
        .filter(models.SOSEvent.patient_id == patient_id)
        .order_by(models.SOSEvent.created_at.desc())
        .all()
    )
