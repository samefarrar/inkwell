"""Learning module — voice profile helpers for the writing flywheel."""

import json
import logging

logger = logging.getLogger(__name__)

_MAX_SAMPLES = 3
_MAX_SAMPLE_CHARS = 2000


def format_samples_for_prompt(samples: list) -> str:  # list[StyleSample]
    """Format writing samples as a prompt context block.

    Returns an empty string if no samples are provided, so callers can
    fall back to the static inspo/ examples or omit the block entirely.
    """
    if not samples:
        return ""

    parts: list[str] = []
    for s in samples[:_MAX_SAMPLES]:
        title = s.title or "Untitled"
        excerpt = s.content[:_MAX_SAMPLE_CHARS]
        parts.append(f"SAMPLE — {title}:\n{excerpt}")

    joined = "\n\n---\n\n".join(parts)
    return "WRITING SAMPLES (match this writer's voice and style closely):\n\n" + joined


def format_voice_profile_for_prompt(profile: dict) -> str:
    """Format a stored voice profile dict as a prompt context block.

    profile keys: voice_descriptors, structural_signature, red_flags, strengths
    """
    lines: list[str] = ["WRITER'S VOICE PROFILE:"]

    descriptors = profile.get("voice_descriptors", [])
    if descriptors:
        lines.append("Voice: " + "; ".join(descriptors))

    sig = profile.get("structural_signature", "")
    if sig:
        lines.append(f"Structure: {sig}")

    red_flags = profile.get("red_flags", [])
    if red_flags:
        lines.append("Weaknesses to avoid: " + "; ".join(red_flags))

    strengths = profile.get("strengths", [])
    if strengths:
        lines.append("Strengths to reinforce: " + "; ".join(strengths))

    return "\n".join(lines)


def load_voice_profile(user_id: int, style_id: int) -> dict | None:
    """Load a stored voice profile from the Preference table.

    Returns None if no profile has been analyzed yet.
    """
    from sqlmodel import select

    from proof_editor.db import db_session
    from proof_editor.models.preference import Preference

    key = f"voice:{style_id}:profile"
    with db_session() as db:
        pref = db.exec(
            select(Preference)
            .where(Preference.user_id == user_id)
            .where(Preference.key == key)
        ).first()

        if not pref:
            return None

        try:
            return json.loads(pref.value)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Corrupt voice profile for style %d", style_id)
            return None


def save_voice_profile(user_id: int, style_id: int, profile: dict) -> None:
    """Upsert a voice profile dict into the Preference table."""
    from datetime import UTC, datetime

    from sqlmodel import select

    from proof_editor.db import db_session
    from proof_editor.models.preference import Preference

    key = f"voice:{style_id}:profile"
    value = json.dumps(profile)

    with db_session() as db:
        pref = db.exec(
            select(Preference)
            .where(Preference.user_id == user_id)
            .where(Preference.key == key)
        ).first()

        if pref:
            pref.value = value
            pref.updated_at = datetime.now(UTC)
        else:
            pref = Preference(user_id=user_id, key=key, value=value)
            db.add(pref)

        db.commit()
