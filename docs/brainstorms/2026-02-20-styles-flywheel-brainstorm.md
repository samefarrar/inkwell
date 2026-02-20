# Styles Flywheel — Brainstorm

**Date:** 2026-02-20
**Status:** Ready for planning

---

## What We're Building

A fully wired styles flywheel that works for any writer — bloggers, scientists, journalists, newsletter writers — so that every session compounds: Inkwell gets better at writing *in your voice* and *editing to your standards* the more you use it.

The backend flywheel is already complete (voice profile extraction, sample injection into drafts, rule stat distillation from focus mode feedback). The gaps are all in UX: there's no way to select a style, trigger analysis, see the results, or add finished pieces back into your profile.

---

## Why This Approach

Both "writing in my voice" and "editing to my standards" matter equally — they're two sides of the same loop:

1. Add samples → analyze → profile extracted
2. Start session with style → drafts sound like you
3. Focus mode → editorial comments know your weaknesses
4. Accept/reject suggestions → rule stats update
5. Finish piece → add it back as a sample → loop tightens

The key design principle: **samples + light metadata > samples alone > metadata alone > nothing**. The AI should be useful from the very first session, and progressively better with each one.

---

## Key Decisions

### 1. Onboarding prompt replaces the static inspo/ fallback

New users should not get Janan Ganesh or Katie Parrott injected into their first draft. Instead, before starting their first session, they're guided to:

> "Paste 2–3 pieces you've written before. Inkwell will use these to match your voice from the start."

This is a one-time setup step (skippable). If skipped, cold sessions get no style examples — the AI produces task-focused drafts without voice matching. The inspo/ directory is cleared of personal/biased examples; the fallback becomes truly neutral (no examples).

**Implementation path:**
- Detect first session (no styles, no samples)
- Show inline onboarding card on the dashboard before TaskSelector
- Single text area: "Paste something you've written" → creates a default style ("My Writing") and adds as a sample
- "Skip for now" link

### 2. Light structured metadata on styles

Add optional fields alongside name/description:

- **Audience** (free text, e.g. "ML researchers", "general public", "B2B marketers")
- **Tone** (pill select: Formal / Conversational / Academic / Technical / Creative)
- **Domain** (free text, e.g. "machine learning", "personal finance", "food science")

These feed into the voice profile prompt and the draft generation system prompt even before any samples are uploaded. For a scientific writer with no samples, `Tone: Academic, Domain: neuroscience, Audience: peer reviewers` already changes how the AI drafts — word choice, hedging language, passive voice tolerance, citation awareness.

**Domain also gates which deterministic style rules are active:**
- Passive voice checker → **disabled** for `Tone: Academic` or `Tone: Technical` (passive is often correct in scientific writing)
- Filler words → active always
- Oxford comma → active always

### 3. Style picker on the session start screen

The TaskSelector shows the user's styles as a compact selector (default: "My Writing" or most recently used). Starting a session with a style selected:
- Sends `style_id` in `task.select` WS message
- Shows an active style chip throughout the session ("Writing as: My Writing")
- The chip is clickable to switch styles (cancels current session, restarts)

If no styles exist, the picker is replaced with an "Add your voice →" CTA that links to styles onboarding.

### 4. Analyze button + voice profile display in StyleEditor

After adding samples, a prominent "Analyze my voice" button triggers `POST /api/styles/{id}/analyze`. While loading, show a progress state ("Reading your samples…"). On completion, display the extracted profile in the StyleEditor:

```
VOICE PROFILE
─────────────────────────────
Voice:       Opens with friction · Concrete over abstract · Short punchy close
Structure:   Starts in medias res, spends middle in evidence, ends with a turn
Strengths:   Earned specificity · Rhythm variation
Avoid:       Hedging with "perhaps" · Abstract nouns as sentence subjects
```

This makes the flywheel *visible* — users understand what the AI has learned about them, and can re-analyze when they add more samples. If the profile is stale (new samples added since last analysis), show a "Re-analyze" nudge.

### 5. Post-session flywheel: save finished piece to profile

After exiting focus mode, show a bottom-of-screen banner:

> "Want to save this piece to your writing profile? It'll help Inkwell match your voice better next time."
> [ Save to *My Writing* ▾ ]  [ Skip ]

The dropdown lets them pick which style to add it to (or create a new one). This is the key compounding loop — every published piece feeds the next session.

### 6. Style-aware rule engine (domain awareness)

The deterministic style engine currently runs the same 3 rules for everyone. The `Tone` field on a style should suppress rules that conflict with domain conventions:

| Rule | Always on | Suppressed for |
|---|---|---|
| Filler words | ✅ | — |
| Oxford comma | ✅ | — |
| Passive voice | ✅ by default | `Tone: Academic` or `Tone: Technical` |

This is a small change with a big impact for scientific/technical writers who would otherwise get flagged constantly for correct passive constructions.

---

## Scope

**In scope:**
- Onboarding prompt for first-time users (replaces inspo/ fallback)
- Light structured metadata on styles (audience, tone, domain)
- Style picker on TaskSelector (compact, defaults to last used)
- Analyze button + voice profile display in StyleEditor
- Post-session save-to-profile banner
- Domain-aware rule suppression (passive voice for Academic/Technical)
- Active style chip during session

**Out of scope (for now):**
- Multiple styles per session (one style per session is enough)
- Style sharing / templates library
- Automated re-analysis triggers
- Style analytics dashboard (accept/reject rates per style)
- Version history for voice profiles

---

## Open Questions

*All resolved during brainstorm — none remaining.*

---

## Resolved Questions

| Question | Decision |
|---|---|
| Writing in voice vs. editing to standards? | Both equally — they're the same loop |
| Cold start experience? | Onboarding prompt to paste own samples |
| Style structure: metadata vs. sample-only? | Light structured metadata (audience, tone, domain) |
| inspo/ files — neutral fallback or personal? | Personal to original author; clear them; cold start gets no examples |
| Post-session add to profile? | Always offer it after focus exit |
