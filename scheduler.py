"""
Background scheduler using APScheduler.

Responsibilities:
  - Every minute: scan active medications and create MedicationLog "due"
    entries + send reminder notifications close to their scheduled time.
  - Daily: remind patients who haven't submitted a check-in yet.
  - Daily: flag missed medications (not marked taken 60+ min after due time)
    and raise an Alert for adherence concerns.

This is intentionally simple/polling-based for portability (works with
SQLite in dev). For production scale, replace the polling loop with a
task queue (Celery/RQ) + a proper notification worker.
"""
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app import models
from app.services.notification_service import _send_sms, _send_email, create_alert

scheduler = BackgroundScheduler()


def _minute_now_str() -> str:
    return datetime.now().strftime("%H:%M")


def check_medication_reminders():
    db = SessionLocal()
    try:
        now = datetime.now()
        current_hm = now.strftime("%H:%M")
        meds = db.query(models.Medication).filter(models.Medication.active == True).all()  # noqa: E712
        for med in meds:
            if not med.times:
                continue
            times = [t.strip() for t in med.times.split(",") if t.strip()]
            if current_hm not in times:
                continue

            # avoid duplicate log for same scheduled minute
            scheduled_dt = now.replace(second=0, microsecond=0)
            existing = (
                db.query(models.MedicationLog)
                .filter(
                    models.MedicationLog.medication_id == med.id,
                    models.MedicationLog.scheduled_time == scheduled_dt,
                )
                .first()
            )
            if existing:
                continue

            log = models.MedicationLog(
                medication_id=med.id,
                patient_id=med.patient_id,
                scheduled_time=scheduled_dt,
                taken=False,
            )
            db.add(log)
            db.commit()

            patient = db.query(models.User).filter(models.User.id == med.patient_id).first()
            if patient:
                message = f"Reminder: time to take {med.name} ({med.dosage or 'as prescribed'})."
                if patient.phone:
                    _send_sms(patient.phone, message)
                if patient.email:
                    _send_email(patient.email, "Medication Reminder", message)
    finally:
        db.close()


def check_missed_medications():
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(minutes=60)
        missed_logs = (
            db.query(models.MedicationLog)
            .filter(
                models.MedicationLog.taken == False,  # noqa: E712
                models.MedicationLog.scheduled_time < cutoff,
                models.MedicationLog.scheduled_time > cutoff - timedelta(hours=6),
            )
            .all()
        )
        for log in missed_logs:
            patient = db.query(models.User).filter(models.User.id == log.patient_id).first()
            med = db.query(models.Medication).filter(models.Medication.id == log.medication_id).first()
            if not patient or not med:
                continue
            already_alerted = (
                db.query(models.Alert)
                .filter(
                    models.Alert.source_type == "medication",
                    models.Alert.source_id == log.id,
                )
                .first()
            )
            if already_alerted:
                continue
            create_alert(
                db,
                patient,
                source_type="medication",
                source_id=log.id,
                severity=models.RiskLevel.MILD_CONCERN,
                message=f"{patient.full_name} missed a scheduled dose of {med.name} at "
                f"{log.scheduled_time.strftime('%Y-%m-%d %H:%M')}.",
            )
    finally:
        db.close()


def check_missing_daily_checkins():
    db = SessionLocal()
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        patients = db.query(models.User).filter(models.User.role == models.UserRole.PATIENT).all()
        for patient in patients:
            checkin_today = (
                db.query(models.CheckIn)
                .filter(models.CheckIn.patient_id == patient.id, models.CheckIn.created_at >= today_start)
                .first()
            )
            if checkin_today:
                continue
            if patient.phone:
                _send_sms(patient.phone, "Friendly reminder: please complete your daily recovery check-in.")
            if patient.email:
                _send_email(
                    patient.email,
                    "Daily Check-in Reminder",
                    "You haven't completed today's recovery check-in yet. It only takes a minute!",
                )
    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(check_medication_reminders, "interval", minutes=1, id="med_reminders", replace_existing=True)
    scheduler.add_job(check_missed_medications, "interval", minutes=15, id="missed_meds", replace_existing=True)
    scheduler.add_job(
        check_missing_daily_checkins, "cron", hour=19, minute=0, id="checkin_reminder", replace_existing=True
    )
    scheduler.start()
