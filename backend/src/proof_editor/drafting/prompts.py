"""Draft generation prompts — angle-specific instructions."""

ANGLE_MAP: dict[str, list[str]] = {
    "review": [
        "Atmosphere-led",
        "Subject-led",
        "Recommendation-led",
    ],
    "essay": ["Thesis-led", "Narrative-led", "Contrarian-led"],
    "newsletter": ["Insight-led", "Story-led", "Tactical-led"],
    "landing_page": [
        "Benefit-led",
        "Social-proof-led",
        "Problem-led",
    ],
    "blog_post": ["Personal-led", "How-to-led", "Opinion-led"],
}

DRAFT_SYSTEM_PROMPT = """\
You are an expert writer creating a {task_type} about \
"{topic}" using the {angle} angle.

INTERVIEW MATERIAL:
{interview_summary}

KEY DETAILS:
{key_material}

{examples_context}

INSTRUCTIONS:
- Write in the {angle} style: {angle_instruction}
- Target 300-500 words
- Use specific details from the interview material
- Follow the Every Write Style Guide:
  * Oxford comma always
  * Em dash (—) with no spaces, max twice per paragraph
  * Active voice preferred
  * Numbers: spell out 1-9, numerals for 10+
  * Cut filler words: "actually", "very", "just", "really"
- Do not use HTML tags or formatting. Output plain text only.
- Make it compelling and publication-ready
- Include a title

Write the draft now. Output the title on the first line, \
then a blank line, then the body."""

ANGLE_INSTRUCTIONS: dict[str, str] = {
    # Review angles
    "Atmosphere-led": (
        "Open with the setting, mood, and sensory details. "
        "Let the reader feel like they're there before "
        "discussing the subject directly."
    ),
    "Subject-led": (
        "Lead with the subject itself—what makes it special, "
        "distinctive, or worth noting. Direct and evaluative."
    ),
    "Recommendation-led": (
        "Frame as a recommendation to a friend. "
        "Conversational, opinionated, and practical."
    ),
    # Essay angles
    "Thesis-led": (
        "Open with a clear thesis statement. Build the "
        "argument logically with evidence from the interview."
    ),
    "Narrative-led": (
        "Open with a story or anecdote. Use narrative structure to make the point."
    ),
    "Contrarian-led": (
        "Challenge conventional wisdom. Open with what most "
        "people think, then reveal a different perspective."
    ),
    # Newsletter angles
    "Insight-led": (
        "Lead with a surprising insight or data point. "
        "Build outward from the 'aha' moment."
    ),
    "Story-led": (
        "Lead with a personal story or case study. Extract the lesson at the end."
    ),
    "Tactical-led": (
        "Lead with actionable advice. What can the reader "
        "do differently starting today?"
    ),
    # Landing page angles
    "Benefit-led": (
        "Lead with the primary benefit to the user. "
        "What transformation will they experience?"
    ),
    "Social-proof-led": (
        "Lead with evidence—who uses this, what results they got, why it's trusted."
    ),
    "Problem-led": (
        "Lead with the pain point. Agitate the problem, then present the solution."
    ),
    # Blog post angles
    "Personal-led": (
        "Write from personal experience. First-person, vulnerable, relatable."
    ),
    "How-to-led": (
        "Structure as a practical guide. Clear steps, "
        "actionable advice, concrete examples."
    ),
    "Opinion-led": ("Take a strong stance. Be direct and bold about your perspective."),
}


def get_angles(task_type: str) -> list[str]:
    """Get the 3 draft angles for a given task type."""
    return ANGLE_MAP.get(task_type, ANGLE_MAP["essay"])


def build_draft_prompt(
    task_type: str,
    topic: str,
    angle: str,
    interview_summary: str,
    key_material: list[str],
    examples_context: str,
) -> str:
    """Build the full prompt for a single draft."""
    angle_instruction = ANGLE_INSTRUCTIONS.get(angle, "Write naturally.")
    key_material_str = "\n".join(f"- {item}" for item in key_material)

    return DRAFT_SYSTEM_PROMPT.format(
        task_type=task_type,
        topic=topic,
        angle=angle,
        interview_summary=interview_summary,
        key_material=key_material_str,
        examples_context=examples_context,
        angle_instruction=angle_instruction,
    )
