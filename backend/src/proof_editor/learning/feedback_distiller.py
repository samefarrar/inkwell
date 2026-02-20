"""Feedback distiller — aggregates session feedback into per-style rule statistics.

Called fire-and-forget after focus.exit. Tallies accepted/rejected suggestions
by rule_id and stores running stats in the Preference table so future editorial
sessions know which rules the user consistently applies vs. dismisses.
"""

import json
import logging

logger = logging.getLogger(__name__)


def distill_session_feedback(user_id: int, style_id: int, session_id: int) -> None:
    """Aggregate feedback from a session into style rule stats.

    Reads Feedback rows for the session, updates running accept/reject tallies
    stored at ``voice:{style_id}:rule_stats`` in the Preference table.

    Designed to run in a fire-and-forget asyncio task — does not raise.
    """
    try:
        from sqlmodel import select

        from proof_editor.db import db_session
        from proof_editor.models.feedback import Feedback
        from proof_editor.models.preference import Preference

        stats_key = f"voice:{style_id}:rule_stats"

        with db_session() as db:
            # Load existing stats
            pref = db.exec(
                select(Preference)
                .where(Preference.user_id == user_id)
                .where(Preference.key == stats_key)
            ).first()

            stats: dict[str, dict[str, int]] = {}
            if pref:
                try:
                    stats = json.loads(pref.value)
                except (json.JSONDecodeError, AttributeError):
                    stats = {}

            # Load session feedback
            feedbacks = db.exec(
                select(Feedback).where(Feedback.session_id == session_id)
            ).all()

            if not feedbacks:
                logger.debug("No feedback to distill for session %d", session_id)
                return

            # Tally by rule_id
            for fb in feedbacks:
                rule = fb.rule_id or "unknown"
                if rule not in stats:
                    stats[rule] = {"accept": 0, "reject": 0, "dismiss": 0}
                action = fb.action or ("accept" if fb.accepted else "reject")
                if action in stats[rule]:
                    stats[rule][action] += 1
                else:
                    stats[rule][action] = 1

            # Upsert
            value = json.dumps(stats)
            if pref:
                pref.value = value
            else:
                pref = Preference(user_id=user_id, key=stats_key, value=value)
                db.add(pref)
            db.commit()

        accepted_count = sum(fb.accepted for fb in feedbacks)
        logger.info(
            "Distilled %d feedbacks for session %d (style %d): %d accepted, %d not accepted",  # noqa: E501
            len(feedbacks),
            session_id,
            style_id,
            accepted_count,
            len(feedbacks) - accepted_count,
        )

    except Exception:
        logger.exception("Error distilling feedback for session %d", session_id)


def load_rule_stats(user_id: int, style_id: int) -> dict[str, dict[str, int]]:
    """Load accumulated rule stats for a style.

    Returns a dict mapping rule_id → {accept, reject, dismiss} counts.
    """
    from sqlmodel import select

    from proof_editor.db import db_session
    from proof_editor.models.preference import Preference

    key = f"voice:{style_id}:rule_stats"
    with db_session() as db:
        pref = db.exec(
            select(Preference)
            .where(Preference.user_id == user_id)
            .where(Preference.key == key)
        ).first()

        if not pref:
            return {}
        try:
            return json.loads(pref.value)
        except (json.JSONDecodeError, AttributeError):
            return {}


def format_rule_stats_for_prompt(stats: dict[str, dict[str, int]]) -> str:
    """Format rule acceptance stats as a prompt context block.

    Only surfaces rules with enough signal (>= 3 total actions).
    Returns empty string if no signal.
    """
    if not stats:
        return ""

    consistently_applied: list[str] = []
    consistently_dismissed: list[str] = []

    for rule_id, counts in stats.items():
        total = (
            counts.get("accept", 0) + counts.get("reject", 0) + counts.get("dismiss", 0)
        )
        if total < 3:
            continue
        accept_rate = counts.get("accept", 0) / total
        reject_rate = (counts.get("reject", 0) + counts.get("dismiss", 0)) / total
        if accept_rate >= 0.7:
            consistently_applied.append(rule_id)
        elif reject_rate >= 0.7:
            consistently_dismissed.append(rule_id)

    if not consistently_applied and not consistently_dismissed:
        return ""

    lines = ["EDITORIAL PREFERENCES (based on past sessions):"]
    if consistently_applied:
        lines.append(
            "Rules this writer consistently applies: " + ", ".join(consistently_applied)
        )
    if consistently_dismissed:
        lines.append(
            "Rules this writer rarely needs (deprioritise): "
            + ", ".join(consistently_dismissed)
        )
    return "\n".join(lines)
