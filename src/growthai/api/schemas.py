"""Pydantic v2 request/response schemas (feature #12).

Schemas define the API contract and drive the auto-generated Swagger docs. They
are deliberately separate from ORM models (never expose the DB shape directly).
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from growthai.core.domain import Standard


# ---- auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str = ""
    role: str = Field(default="parent", pattern="^(parent|doctor|admin)$")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- patients ----
class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    gender: str = Field(pattern="^(male|female|M|F|m|f)$")
    birth_date: str = ""


class PatientOut(BaseModel):
    id: int
    name: str
    gender: str
    birth_date: str


# ---- analysis ----
class MeasurementIn(BaseModel):
    age_months: float = Field(ge=0, le=240, description="Age in months (0-240).")
    height_cm: float = Field(ge=30, le=230)
    weight_kg: float = Field(ge=1, le=300)
    gender: str = Field(pattern="^(male|female|M|F|m|f)$")
    standard: Standard = Standard.WHO


class AnalyzeRequest(MeasurementIn):
    name: str = "Anonymous"
    patient_id: int | None = None
    save: bool = False


# ---- chat ----
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ChatResponseOut(BaseModel):
    answer: str
    sources: list[str]
    confidence: float
    provider: str


# ---- report ----
class ReportRequest(MeasurementIn):
    name: str = "Anonymous"
    doctor_notes: str = ""


class ReportOut(BaseModel):
    report_id: str
    html_available: bool
    pdf_available: bool
    download_url: str
