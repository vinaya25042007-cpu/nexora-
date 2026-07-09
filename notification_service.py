"""
Notification service: creates in-app Alert records and dispatches
SMS/email notifications to caregivers + the assigned doctor.

SMS/email sending is stubbed with pluggable functions (`_send_sms`,
`_send_email`) that log to console by default. Wire up Twilio / SendGrid
(or any provider) inside those two functions using the credentials in
app.config.settings — the rest of the system doesn't need to change.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app import models
from app.config import settings


def _send_sms(to_number: str, message: str) -> None:
    if not settings.TWILIO_ACCOUNT_SID:
        print(f"[SMS-STUB] to={to_number}: {message}")
        return
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to=to_number)
    except Exception as e:
        print(f"[SMS-ERROR] {e}")


def _send_email(to_email: str, subject: str, message: str) -> None:
    if not settings.SENDGRID_API_KEY:
        print(f"[EMAIL-STUB] to={to_email} subject={subject}: {message}")
        return
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        mail = Mail(
            from_email=settings.ALERT_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=message,
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(mail)
    except Exception as e:
        print(f"[EMAIL-ERROR] {e}")


def create_alert(
    db: Session,
    patient: models.User,
    source_type: str,
    message: str,
    severity: models.RiskLevel = models.RiskLevel.MILD_CONCERN,
    source_id: Optional[str] = None,
) -> models.Alert:
    alert = models.Alert(
        patient_id=patient.id,
        source_type=source_type,
        source_id=source_id,
        severity=severity,
        message=message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    notify_caregivers_and_doctor(db, patient, message, severity)
    return alert


def notify_caregivers_and_doctor(
    db: Session, patient: models.User, message: str, severity: models.RiskLevel
) -> None:
    subject = f"[Recovery Assistant] {severity.value.upper()} alert for {patient.full_name}"

    # Notify assigned doctor
    if patient.assigned_doctor_id:
        doctor = db.query(models.User).filter(models.User.id == patient.assigned_doctor_id).first()
        if doctor:
            if doctor.email:
                _send_email(doctor.email, subject, message)
            if doctor.phone and severity == models.RiskLevel.URGENT:
                _send_sms(doctor.phone, message)

    # Notify linked caregivers
    links = (
        db.query(models.CaregiverLink)
        .filter(models.CaregiverLink.patient_id == patient.id)
        .all()
    )
    for link in links:
        caregiver = db.query(models.User).filter(models.User.id == link.caregiver_id).first()
        if not caregiver:
            continue
        if link.notify_email and caregiver.email:
            _send_email(caregiver.email, subject, message)
        if link.notify_sms and caregiver.phone:
            _send_sms(caregiver.phone, message)
