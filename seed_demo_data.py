"""
Optional helper: creates a demo doctor + patient + caregiver so you can
explore the API immediately after starting the server.

Usage:
    python seed_demo_data.py
"""
from app.database import SessionLocal, Base, engine
from app import models
from app.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    doctor = db.query(models.User).filter(models.User.email == "doctor@demo.com").first()
    if not doctor:
        doctor = models.User(
            full_name="Dr. Asha Menon",
            email="doctor@demo.com",
            phone="+911234567890",
            hashed_password=hash_password("password123"),
            role=models.UserRole.DOCTOR,
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        print(f"Created doctor: {doctor.email} / password123 (id={doctor.id})")

    caregiver = db.query(models.User).filter(models.User.email == "caregiver@demo.com").first()
    if not caregiver:
        caregiver = models.User(
            full_name="Ravi Kumar",
            email="caregiver@demo.com",
            phone="+911234567891",
            hashed_password=hash_password("password123"),
            role=models.UserRole.CAREGIVER,
        )
        db.add(caregiver)
        db.commit()
        db.refresh(caregiver)
        print(f"Created caregiver: {caregiver.email} / password123 (id={caregiver.id})")

    patient = db.query(models.User).filter(models.User.email == "patient@demo.com").first()
    if not patient:
        patient = models.User(
            full_name="Priya Sharma",
            email="patient@demo.com",
            phone="+911234567892",
            hashed_password=hash_password("password123"),
            role=models.UserRole.PATIENT,
            assigned_doctor_id=doctor.id,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        print(f"Created patient: {patient.email} / password123 (id={patient.id})")

    link = (
        db.query(models.CaregiverLink)
        .filter(models.CaregiverLink.patient_id == patient.id, models.CaregiverLink.caregiver_id == caregiver.id)
        .first()
    )
    if not link:
        db.add(models.CaregiverLink(patient_id=patient.id, caregiver_id=caregiver.id, relationship_label="son"))
        db.commit()
        print("Linked caregiver to patient")

    print("\nDemo data ready. Login with any of the above email/password123 pairs at POST /auth/login")
finally:
    db.close()
