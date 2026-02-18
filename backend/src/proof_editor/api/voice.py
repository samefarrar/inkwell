"""Voice token endpoint for AssemblyAI streaming transcription."""

import os
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/voice", tags=["voice"])

_last_token_time: datetime | None = None

ASSEMBLYAI_TOKEN_URL = "https://streaming.assemblyai.com/v3/token"
TOKEN_COOLDOWN_SECONDS = 10
TOKEN_LIFETIME_SECONDS = 60


@router.get("/token")
async def create_voice_token() -> dict[str, str]:
    """Generate a temporary AssemblyAI token (60s lifetime, rate-limited)."""
    global _last_token_time
    now = datetime.now()
    if _last_token_time and (now - _last_token_time).total_seconds() < TOKEN_COOLDOWN_SECONDS:
        raise HTTPException(429, "Token rate limited — try again in 10s")

    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "AssemblyAI API key not configured")

    _last_token_time = now

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            ASSEMBLYAI_TOKEN_URL,
            params={"expires_in_seconds": TOKEN_LIFETIME_SECONDS},
            headers={"Authorization": api_key},
        )
        if resp.status_code != 200:
            raise HTTPException(502, "Failed to get AssemblyAI token")
        return {"token": resp.json()["token"]}
