"""Authentication routes: register + login (feature #12)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from growthai.api.schemas import Token, UserCreate, UserOut
from growthai.api.security import create_access_token, hash_password, verify_password
from growthai.db.models import User
from growthai.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.email, user.role)
    return Token(access_token=token, user=_to_out(user))


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    # OAuth2 form uses 'username'; we treat it as the email.
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(user.email, user.role)
    return Token(access_token=token, user=_to_out(user))
