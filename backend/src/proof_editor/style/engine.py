"""Style rule engine — deterministic analysis of writing for common issues.

Runs regex-based rules for filler words, passive voice, and Oxford comma.
Returns structured violations with character offsets for frontend positioning.
"""

import functools
import re
import uuid
from dataclasses import dataclass


@dataclass
class StyleViolation:
    id: str
    quote: str
    start: int
    end: int
    replacement: str
    explanation: str
    rule_id: str


# --- Pre-compiled patterns ---

# Filler words: match whole words only, case-insensitive
_FILLER_WORDS = ["very", "really", "just", "actually", "basically", "literally"]
_FILLER_PATTERN = re.compile(r"\b(" + "|".join(_FILLER_WORDS) + r")\b", re.IGNORECASE)

# Passive voice: "was/were/been/being/is/are + past participle (-ed/-en/-t)"
_PASSIVE_PATTERN = re.compile(
    r"\b(was|were|been|being|is|are)\s+(\w+(?:ed|en|t))\b", re.IGNORECASE
)

# Oxford comma: "A, B and C" (missing comma before "and")
# Matches "word, word and word" without a comma before "and"
_OXFORD_PATTERN = re.compile(r"(\w+),\s+(\w+)\s+(and|or)\s+(\w+)", re.IGNORECASE)


def _check_filler_words(text: str) -> list[StyleViolation]:
    violations = []
    for match in _FILLER_PATTERN.finditer(text):
        word = match.group(0)
        violations.append(
            StyleViolation(
                id=str(uuid.uuid4()),
                quote=word,
                start=match.start(),
                end=match.end(),
                replacement="",
                explanation=(
                    f'"{word}" is a filler word that weakens '
                    "your writing. Consider removing it."
                ),
                rule_id="filler_words",
            )
        )
    return violations


def _check_passive_voice(text: str) -> list[StyleViolation]:
    violations = []
    for match in _PASSIVE_PATTERN.finditer(text):
        full = match.group(0)
        violations.append(
            StyleViolation(
                id=str(uuid.uuid4()),
                quote=full,
                start=match.start(),
                end=match.end(),
                replacement="",
                explanation=(
                    "This may be passive voice. Consider "
                    "rewriting in active voice for more "
                    "direct, engaging prose."
                ),
                rule_id="passive_voice",
            )
        )
    return violations


def _check_oxford_comma(text: str) -> list[StyleViolation]:
    violations = []
    for match in _OXFORD_PATTERN.finditer(text):
        full = match.group(0)
        # Check that there's no comma before "and"/"or"
        conjunction = match.group(3)
        second_word = match.group(2)
        # The pattern already matches missing comma cases
        fixed = full.replace(
            f"{second_word} {conjunction}",
            f"{second_word}, {conjunction}",
        )
        violations.append(
            StyleViolation(
                id=str(uuid.uuid4()),
                quote=full,
                start=match.start(),
                end=match.end(),
                replacement=fixed,
                explanation=(
                    "Consider adding an Oxford comma "
                    f'before "{conjunction}" for clarity.'
                ),
                rule_id="oxford_comma",
            )
        )
    return violations


@functools.lru_cache(maxsize=256)
def _analyze_cached(text: str) -> tuple[StyleViolation, ...]:
    violations: list[StyleViolation] = []
    violations.extend(_check_filler_words(text))
    violations.extend(_check_passive_voice(text))
    violations.extend(_check_oxford_comma(text))
    violations.sort(key=lambda v: v.start)
    return tuple(violations)


def analyze(text: str) -> list[StyleViolation]:
    """Run all style rules on the given text.

    Returns a list of violations with character offsets.
    Uses LRU cache to skip redundant analysis on identical text.
    """
    return list(_analyze_cached(text))
