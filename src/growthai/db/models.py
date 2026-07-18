"""ORM models (feature #11).

Mirrors the ER diagram in docs/ARCHITECTURE.md: users own patients; patients
have measurements; measurements yield analyses; analyses contain predictions;
patients accumulate reports. Roles support the multi-user system (feature #10).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from growthai.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(20), default="parent")  # parent|doctor|admin
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    patients: Mapped[list[Patient]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    gender: Mapped[str] = mapped_column(String(10))
    birth_date: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    owner: Mapped[User] = relationship(back_populates="patients")
    measurements: Mapped[list[Measurement]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    reports: Mapped[list[Report]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    age_months: Mapped[float] = mapped_column(Float)
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    patient: Mapped[Patient] = relationship(back_populates="measurements")
    analysis: Mapped[Analysis | None] = relationship(
        back_populates="measurement", cascade="all, delete-orphan", uselist=False
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    measurement_id: Mapped[int] = mapped_column(ForeignKey("measurements.id"), index=True)
    bmi: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(30))
    z_score: Mapped[float] = mapped_column(Float)
    percentile: Mapped[float] = mapped_column(Float)
    standard: Mapped[str] = mapped_column(String(10))
    overall_risk: Mapped[str] = mapped_column(String(10), default="Low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    measurement: Mapped[Measurement] = relationship(back_populates="analysis")
    predictions: Mapped[list[Prediction]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    horizon: Mapped[str] = mapped_column(String(20))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    bmi: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)

    analysis: Mapped[Analysis] = relationship(back_populates="predictions")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    report_id: Mapped[str] = mapped_column(String(20), index=True)
    html_path: Mapped[str] = mapped_column(Text, default="")
    pdf_path: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    patient: Mapped[Patient] = relationship(back_populates="reports")
