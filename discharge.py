import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.config import settings
from app.dependencies import get_current_user, ensure_patient_access
from app.services import ai_service

router = APIRouter(prefix="/discharge-summaries", tags=["Discharge Summary & Recovery Plan"])


def _extract_text_from_upload(path: str) -> str:
    """Minimal text extraction. Supports .txt directly; for PDFs/images this
    is a placeholder — plug in an OCR pipeline (e.g. pytesseract, or a PDF
    text extractor) here for production use."""
    if path.lower().endswith(".txt"):
        with open(path, "r", errors="ignore") as f:
            return f.read()
    return (
        "[Binary document uploaded — plug in OCR/PDF-text extraction in "
        "discharge.py:_extract_text_from_upload to populate this automatically. "
        "For now the AI extraction step will work from the filename/context only.]"
    )


@router.post("/upload", response_model=schemas.RecoveryPlanOut, status_code=201)
def upload_discharge_summary(
    patient_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ensure_patient_access(patient_id, current_user, db)
    patient = db.query(models.User).filter(models.User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    ext = os.path.splitext(file.filename)[1] or ".bin"
    fname = f"{uuid.uuid4()}{ext}"
    dest_dir = os.path.join(settings.UPLOAD_DIR, "discharge_summaries")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, fname)
    with open(dest_path, "wb") as f:
        f.write(file.file.read())

    raw_text = _extract_text_from_upload(dest_path)

    extracted = ai_service.extract_discharge_summary(raw_text)

    ds = models.DischargeSummary(
        patient_id=patient_id,
        file_path=dest_path,
        raw_text=raw_text,
        surgery_type=extracted.get("surgery_type"),
        surgery_date=extracted.get("surgery_date"),
        ai_extracted_json=json.dumps(extracted),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)

    # Deactivate previous plans, create new active plan
    db.query(models.RecoveryPlan).filter(
        models.RecoveryPlan.patient_id == patient_id, models.RecoveryPlan.is_active == True  # noqa: E712
    ).update({"is_active": False})

    summary_text = ai_service.generate_recovery_plan_summary(extracted)

    plan = models.RecoveryPlan(
        patient_id=patient_id,
        discharge_summary_id=ds.id,
        summary_text=summary_text,
        diet_recommendations=json.dumps(extracted.get("diet_recommendations", [])),
        rehab_plan=json.dumps(extracted.get("rehab_exercises", [])),
        follow_up_schedule=json.dumps(extracted.get("follow_up_appointments", [])),
        precautions=json.dumps(
            (extracted.get("precautions", []) or []) + (extracted.get("warning_signs", []) or [])
        ),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Auto-create medication records from extracted data
    for med in extracted.get("medications", []) or []:
        db.add(
            models.Medication(
                recovery_plan_id=plan.id,
                patient_id=patient_id,
                name=med.get("name", "Unnamed medication"),
                dosage=med.get("dosage"),
                frequency_per_day=med.get("frequency_per_day") or 1,
                instructions=med.get("instructions"),
                active=True,
            )
        )
    db.commit()

    out = schemas.RecoveryPlanOut.model_validate(plan)
    out.diet_recommendations = extracted.get("diet_recommendations", [])
    out.rehab_plan = extracted.get("rehab_exercises", [])
    out.follow_up_schedule = extracted.get("follow_up_appointments", [])
    out.precautions = (extracted.get("precautions", []) or []) + (extracted.get("warning_signs", []) or [])
    return out


@router.get("/patient/{patient_id}", response_model=list[schemas.DischargeSummaryOut])
def list_discharge_summaries(
    patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_patient_access(patient_id, current_user, db)
    return (
        db.query(models.DischargeSummary)
        .filter(models.DischargeSummary.patient_id == patient_id)
        .order_by(models.DischargeSummary.uploaded_at.desc())
        .all()
    )


@router.get("/patient/{patient_id}/active-plan", response_model=schemas.RecoveryPlanOut)
def get_active_plan(
    patient_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    ensure_patient_access(patient_id, current_user, db)
    plan = (
        db.query(models.RecoveryPlan)
        .filter(models.RecoveryPlan.patient_id == patient_id, models.RecoveryPlan.is_active == True)  # noqa: E712
        .order_by(models.RecoveryPlan.generated_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No active recovery plan found")

    out = schemas.RecoveryPlanOut.model_validate(plan)
    out.diet_recommendations = json.loads(plan.diet_recommendations or "[]")
    out.rehab_plan = json.loads(plan.rehab_plan or "[]")
    out.follow_up_schedule = json.loads(plan.follow_up_schedule or "[]")
    out.precautions = json.loads(plan.precautions or "[]")
    return out
