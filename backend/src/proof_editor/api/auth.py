"""Auth REST endpoints — register, login, logout, me."""

import os
from asyncio import to_thread
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import select

from proof_editor.auth_deps import JWT_ALGORITHM, _get_secret_key, get_current_user
from proof_editor.db import db_session
from proof_editor.models.user import User, UserCreate, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


pwd_hash = PasswordHash.recommended()

TOKEN_LIFETIME_HOURS = 24

# Dummy hash for timing-attack prevention
_DUMMY_HASH = pwd_hash.hash("dummypassword12345678")


def _create_token(user: User) -> str:
    secret = _get_secret_key()
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
        "exp": datetime.now(UTC) + timedelta(hours=TOKEN_LIFETIME_HOURS),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def _set_auth_cookie(response: Response, token: str) -> None:
    is_dev = os.environ.get("ENV", "development") == "development"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=not is_dev,
        max_age=86400,
        path="/",
    )


@router.post("/register")
async def register(body: UserCreate, response: Response) -> dict:
    """Create a new account and auto-login."""
    hashed = await to_thread(pwd_hash.hash, body.password)
    with db_session() as db:
        existing = db.exec(select(User).where(User.email == body.email)).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        user = User(
            email=body.email,
            name=body.name,
            hashed_password=hashed,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = _create_token(user)
        _set_auth_cookie(response, token)
        return {"token": token, "user": UserRead.model_validate(user).model_dump()}


@router.post("/login")
async def login(body: LoginRequest, response: Response) -> dict:
    """Validate credentials and return JWT."""
    with db_session() as db:
        user = db.exec(
            select(User).where(User.email == body.email.strip().lower())
        ).first()

    if not user:
        # Timing-attack prevention: hash dummy password
        await to_thread(pwd_hash.verify, body.password, _DUMMY_HASH)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    valid = await to_thread(pwd_hash.verify, body.password, user.hashed_password)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _create_token(user)
    _set_auth_cookie(response, token)
    return {"token": token, "user": UserRead.model_validate(user).model_dump()}


@router.post("/logout")
def logout(response: Response) -> dict:
    """Clear auth cookie."""
    response.delete_cookie("access_token", path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    """Return current user profile."""
    return user
