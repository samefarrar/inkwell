"""User preferences REST endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from proof_editor.auth_deps import get_current_user
from proof_editor.learning import load_preference, save_preference
from proof_editor.models.user import User

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("")
def get_preferences(user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Return key preferences for the current user."""
    onboarding = load_preference(user.id, "user:onboarding_completed")  # type: ignore[arg-type]
    last_style_raw = load_preference(user.id, "user:last_style_id")  # type: ignore[arg-type]
    last_style_id = int(last_style_raw) if last_style_raw else None
    return {
        "onboarding_completed": onboarding == "true",
        "last_style_id": last_style_id,
    }


@router.post("/onboarding")
def complete_onboarding(user: User = Depends(get_current_user)) -> dict[str, str]:
    """Mark onboarding as completed for the current user."""
    save_preference(user.id, "user:onboarding_completed", "true")  # type: ignore[arg-type]
    return {"status": "ok"}
