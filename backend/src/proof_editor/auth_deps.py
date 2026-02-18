"""Auth dependencies — JWT extraction and user resolution."""

import os

import jwt
from fastapi import Depends, HTTPException, Request
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session

from proof_editor.db import get_db
from proof_editor.models.user import User

JWT_ALGORITHM = "HS256"


def _get_secret_key() -> str:
    key = os.environ.get("JWT_SECRET_KEY", "")
    if len(key) < 32:
        msg = "JWT_SECRET_KEY must be at least 32 characters"
        raise RuntimeError(msg)
    return key


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Extract user from httpOnly cookie JWT. 401 if missing/invalid."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        secret = _get_secret_key()
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
