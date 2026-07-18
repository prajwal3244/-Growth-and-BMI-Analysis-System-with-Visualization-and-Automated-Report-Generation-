"""Patient CRUD + history (features #10, #11)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from growthai.api.deps import get_current_user
from growthai.api.schemas import PatientCreate, PatientOut
from growthai.core.domain import Gender
from growthai.db import models
from growthai.db.session import get_db

router = APIRouter(prefix="/patients", tags=["patients"])


def _out(p: models.Patient) -> PatientOut:
    return PatientOut(id=p.id, name=p.name, gender=p.gender, birth_date=p.birth_date)


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> PatientOut:
    patient = models.Patient(
        user_id=user.id,
        name=payload.name,
        gender=Gender.parse(payload.gender).value,
        birth_date=payload.birth_date,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return _out(patient)


@router.get("", response_model=list[PatientOut])
def list_patients(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
) -> list[PatientOut]:
    rows = db.scalars(select(models.Patient).where(models.Patient.user_id == user.id)).all()
    return [_out(p) for p in rows]


@router.get("/{patient_id}/history")
def patient_history(
    patient_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    patient = db.get(models.Patient, patient_id)
    if not patient or patient.user_id != user.id:
        raise HTTPException(status_code=404, detail="Patient not found")
    history = []
    for meas in sorted(patient.measurements, key=lambda x: x.taken_at):
        entry = {
            "measurement_id": meas.id,
            "age_months": meas.age_months,
            "height_cm": meas.height_cm,
            "weight_kg": meas.weight_kg,
            "taken_at": meas.taken_at.isoformat(),
        }
        if meas.analysis:
            entry["bmi"] = meas.analysis.bmi
            entry["category"] = meas.analysis.category
            entry["percentile"] = meas.analysis.percentile
        history.append(entry)
    return {"patient": _out(patient).model_dump(), "timeline": history}


@router.delete("/{patient_id}", status_code=204)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    patient = db.get(models.Patient, patient_id)
    if not patient or patient.user_id != user.id:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
