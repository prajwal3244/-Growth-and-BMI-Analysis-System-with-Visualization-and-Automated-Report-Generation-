"""Shared FastAPI dependencies: current-user resolution and role guards."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from growthai.api.security import decode_token
from growthai.db.models import User
from growthai.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise _CREDENTIALS_EXC
    user = db.scalar(select(User).where(User.email == payload["sub"]))
    if user is None:
        raise _CREDENTIALS_EXC
    return user


def require_role(*roles: str):
    """Dependency factory that restricts a route to specific roles."""

    def _guard(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(roles)}")
        return user

    return _guard
