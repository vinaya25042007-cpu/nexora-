import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.dependencies import get_current_user, ensure_patient_access
from app.services import cv_service
from app.services.notification_service import create_alert

router = APIRouter(prefix="/wounds", tags=["Wound Monitoring"])


@router.post("/patient/{patient_id}/upload", response_model=schemas.WoundImageOut, status_code=201)
def upload_wound_image(
    patient_id: str,
    day_since_surgery: int | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    patient = db.query(models.User).filter(models.User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    ext = os.path.splitext(file.filename)[1] or ".jpg"
    fname = f"{uuid.uuid4()}{ext}"
    dest_dir = os.path.join(settings.UPLOAD_DIR, "wound_images")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, fname)
    with open(dest_path, "wb") as f:
        f.write(file.file.read())

    wound_image = models.WoundImage(
        patient_id=patient_id, file_path=dest_path, day_since_surgery=day_since_surgery
    )
    db.add(wound_image)
    db.commit()
    db.refresh(wound_image)

    result = cv_service.analyze_wound_image(dest_path)

    analysis = models.WoundAnalysis(
        wound_image_id=wound_image.id,
        patient_id=patient_id,
        risk_level=models.RiskLevel(result["risk_level"]),
        redness_score=result["redness_score"],
        swelling_score=result["swelling_score"],
        discharge_score=result["discharge_score"],
        confidence=result["confidence"],
        findings=json.dumps(result["findings"]),
        recommendation=result["recommendation"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    if analysis.risk_level in (models.RiskLevel.URGENT, models.RiskLevel.MILD_CONCERN):
        create_alert(
            db,
            patient,
            source_type="wound_analysis",
            source_id=analysis.id,
            severity=analysis.risk_level,
            message=(
                f"Wound analysis for {patient.full_name} flagged risk level "
                f"'{analysis.risk_level.value}': {analysis.recommendation}"
            ),
        )

    wound_image.analysis = analysis
    out = schemas.WoundImageOut.model_validate(wound_image)
    out.analysis = schemas.WoundAnalysisOut(
        id=analysis.id,
        wound_image_id=wound_image.id,
        risk_level=analysis.risk_level,
        redness_score=analysis.redness_score,
        swelling_score=analysis.swelling_score,
        discharge_score=analysis.discharge_score,
        confidence=analysis.confidence,
        findings=result["findings"],
        recommendation=analysis.recommendation,
        analyzed_at=analysis.analyzed_at,
    )
    return out


@router.get("/patient/{patient_id}/history", response_model=list[schemas.WoundImageOut])
def wound_history(
    patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_patient_access(patient_id, current_user, db)
    images = (
        db.query(models.WoundImage)
        .filter(models.WoundImage.patient_id == patient_id)
        .order_by(models.WoundImage.uploaded_at.desc())
        .all()
    )
    results = []
    for img in images:
        out = schemas.WoundImageOut.model_validate(img)
        if img.analysis:
            out.analysis = schemas.WoundAnalysisOut(
                id=img.analysis.id,
                wound_image_id=img.id,
                risk_level=img.analysis.risk_level,
                redness_score=img.analysis.redness_score,
                swelling_score=img.analysis.swelling_score,
                discharge_score=img.analysis.discharge_score,
                confidence=img.analysis.confidence,
                findings=json.loads(img.analysis.findings or "[]"),
                recommendation=img.analysis.recommendation,
                analyzed_at=img.analysis.analyzed_at,
            )
        results.append(out)
    return results
