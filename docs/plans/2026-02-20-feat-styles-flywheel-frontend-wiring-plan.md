---
title: "feat: Styles Flywheel — Full Frontend Wiring + Domain-Aware Engine"
type: feat
status: active
date: 2026-02-20
---

# feat: Styles Flywheel — Full Frontend Wiring + Domain-Aware Engine

## Overview

The backend flywheel is complete: voice profile extraction, sample injection into drafts, rule stat distillation from focus feedback. Every session still falls back to hardcoded inspo/ files because the frontend has no way to select a style, trigger analysis, or see the results.

This plan wires the full loop: onboarding → style metadata → style picker → voice-matched drafts → voice-aware editorial → post-session compounding.

---

## Problem Statement

1. **No style selection UI** — `style_id` is always null in `task.select`. Every session uses the static inspo/ fallback (which contains personal writing samples from the original developer, not the user).
2. **No analyze button** — `POST /api/styles/{id}/analyze` exists but is unreachable from the UI. Voice profiles are never generated.
3. **No voice profile display** — Users can't see what the AI has learned about them.
4. **No onboarding** — New users get the personal inspo/ fallback, not their own voice.
5. **Rule engine is tone-blind** — Passive voice flagged for academic writers who use it correctly.
6. **No compounding loop** — Finished pieces aren't offered back as style samples.

---

## Technical Approach

### Architecture

```
Onboarding (one-time)
  └─ OnboardingPrompt.svelte → createStyle + addSample + mark onboarding_completed

TaskSelector (every session)
  └─ Style picker (default: last_style_id Preference key) → task.select{style_id}
       └─ orchestrator._load_examples_context() → voice profile + samples
       └─ orchestrator.handle_focus_enter() → tone → suppressed_rules → engine.analyze()

StyleEditor
  └─ Metadata (tone, audience, domain) → PUT /api/styles/{id}
  └─ Analyze button → POST /api/styles/{id}/analyze → voice profile display

FocusEditor exit
  └─ Banner → POST /api/styles/{id}/samples (content from focus.content)
```

---

## Implementation Phases

### Phase 1: Backend — WritingStyle Metadata + Preferences API

**Goal:** Add tone/audience/domain to `WritingStyle`; add preferences endpoints for onboarding flag + last-used style.

#### `backend/src/proof_editor/models/style.py`

Add three nullable `str` fields to `WritingStyle`:

```python
class WritingStyle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    name: str = Field(max_length=200, index=True)
    description: str = Field(default="", max_length=2000)
    # New metadata fields
    tone: str | None = Field(default=None, max_length=50)       # "Formal" | "Conversational" | "Academic" | "Technical" | "Creative"
    audience: str | None = Field(default=None, max_length=200)  # e.g. "ML researchers", "general public"
    domain: str | None = Field(default=None, max_length=200)    # e.g. "machine learning", "personal finance"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

**Do NOT use `Literal[...]` for tone** — per known SQLModel bug, use `str` with application-level validation.

#### `backend/src/proof_editor/db.py` — Migration

After the `SQLModel.metadata.create_all(engine)` call, add column-safe migrations:

```python
def _migrate_schema(engine):
    with engine.connect() as conn:
        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("writingstyle")}
        for col, ddl in [
            ("tone", "ALTER TABLE writingstyle ADD COLUMN tone TEXT"),
            ("audience", "ALTER TABLE writingstyle ADD COLUMN audience TEXT"),
            ("domain", "ALTER TABLE writingstyle ADD COLUMN domain TEXT"),
        ]:
            if col not in cols:
                conn.execute(text(ddl))
        conn.commit()
```

Call `_migrate_schema(engine)` once at startup, after `create_all`.

#### `backend/src/proof_editor/api/styles.py`

Update `PUT /api/styles/{id}` to accept and save new fields:

```python
class StyleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tone: str | None = None
    audience: str | None = None
    domain: str | None = None

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v):
        allowed = {"Formal", "Conversational", "Academic", "Technical", "Creative", None}
        if v not in allowed:
            raise ValueError(f"tone must be one of {allowed}")
        return v
```

Ensure `GET /api/styles` list and `GET /api/styles/{id}` both return `tone`, `audience`, `domain` in the response.

#### `backend/src/proof_editor/api/preferences.py` — New file

```python
# GET /api/preferences → { "onboarding_completed": bool, "last_style_id": int | None }
# POST /api/preferences/onboarding → marks onboarding_completed = true
```

Reads/writes to the `Preference` table under:
- Key `user:onboarding_completed` — value `"true"`
- Key `user:last_style_id` — value `str(style_id)` or absent

Mount at `/api/preferences` in `main.py`.

#### `backend/src/proof_editor/agent/orchestrator.py`

In `handle_task_select()`, after saving the session, write the last-used style preference:

```python
if self.style_id:
    save_preference(self.user_id, "user:last_style_id", str(self.style_id))
```

Add `save_preference` / `load_preference` helpers alongside the existing `save_voice_profile` / `load_voice_profile` pattern in `learning/__init__.py`.

---

### Phase 2: Style Engine — Domain-Aware Rule Suppression

**Goal:** Suppress passive voice for Academic/Technical styles. Fix LRU cache key to include suppressed rules.

#### `backend/src/proof_editor/style/engine.py`

```python
TONE_SUPPRESSED_RULES: dict[str, frozenset[str]] = {
    "Academic": frozenset({"passive_voice"}),
    "Technical": frozenset({"passive_voice"}),
}

def get_suppressed_rules(tone: str | None) -> frozenset[str]:
    if tone is None:
        return frozenset()
    return TONE_SUPPRESSED_RULES.get(tone, frozenset())

@functools.lru_cache(maxsize=256)
def _analyze_cached(text: str, suppressed: frozenset[str]) -> tuple[StyleViolation, ...]:
    violations: list[StyleViolation] = []
    if "filler_words" not in suppressed:
        violations.extend(_check_filler_words(text))
    if "passive_voice" not in suppressed:
        violations.extend(_check_passive_voice(text))
    if "oxford_comma" not in suppressed:
        violations.extend(_check_oxford_comma(text))
    return tuple(sorted(violations, key=lambda v: v.start))

def analyze(text: str, suppressed: frozenset[str] = frozenset()) -> list[StyleViolation]:
    return list(_analyze_cached(text, suppressed))
```

**Note:** The cache key now includes `suppressed` (a `frozenset`, which is hashable). Two sessions with the same text but different tone will get separate cache entries — correct behaviour.

#### `backend/src/proof_editor/agent/focus_handler.py`

Add `tone: str | None` parameter to `FocusHandler.__init__()`. Pass to `engine.analyze()`:

```python
suppressed = get_suppressed_rules(self.tone)
violations = engine.analyze(stripped_text, suppressed=suppressed)
```

#### `backend/src/proof_editor/agent/orchestrator.py`

In `handle_focus_enter()`, load the style's tone and pass to `FocusHandler`:

```python
tone: str | None = None
if self.style_id:
    style = db.get(WritingStyle, self.style_id)
    if style:
        tone = style.tone

self._focus_handler = FocusHandler(
    ...,
    tone=tone,
)
```

---

### Phase 3: Styles Store + StyleEditor — Metadata & Analyze UI

**Goal:** Wire analyze to the UI; show the voice profile; allow editing tone/audience/domain.

#### `frontend/src/lib/stores/styles.svelte.ts`

Add new interfaces and state:

```typescript
export interface VoiceProfile {
  voice_descriptors: string[];
  structural_signature: string;
  red_flags: string[];
  strengths: string[];
}

export interface WritingStyle {
  id: number;
  name: string;
  description: string;
  tone: string | null;
  audience: string | null;
  domain: string | null;
  created_at: string;
  updated_at: string;
}
```

Add to `StylesStore`:

```typescript
voiceProfile = $state<VoiceProfile | null>(null);
analyzing = $state(false);

async analyzeStyle(id: number): Promise<void> {
  this.analyzing = true;
  try {
    const res = await fetch(`${BASE_API_URL}/api/styles/${id}/analyze`, { method: 'POST' });
    if (res.ok) this.voiceProfile = await res.json();
  } finally {
    this.analyzing = false;
  }
}

async loadVoiceProfile(id: number): Promise<void> {
  const res = await fetch(`${BASE_API_URL}/api/styles/${id}/voice_profile`);
  if (res.ok) this.voiceProfile = await res.json();
  else this.voiceProfile = null;
}
```

Update `loadStyle()` to also call `loadVoiceProfile()` after loading the style.

#### `frontend/src/lib/components/StyleEditor.svelte`

**New metadata section** (below the name/description, above samples):

```
[ Tone ]  ○ Formal  ○ Conversational  ○ Academic  ○ Technical  ○ Creative
[ Audience ]  ___________________________  (free text input)
[ Domain ]    ___________________________  (free text input)
```

Tone pills update immediately on click (debounced `PUT /api/styles/{id}`). Audience/domain save on blur.

**Analyze section** (below samples list):

```
[ Analyze my voice → ]   (disabled if 0 samples or analyzing)
  ↕ while analyzing: spinner + "Reading your samples…"
  ↕ after analysis: voice profile card
```

**Voice profile card** (shown when `styles.voiceProfile` is not null):

```
VOICE PROFILE  [ Re-analyze ]

Voice        Opens with friction · Concrete over abstract · Short punchy close
Structure    Starts in medias res, evidence in the middle, ends with a turn
Strengths    Earned specificity · Rhythm variation
Avoid        Hedging with "perhaps" · Abstract nouns as sentence subjects
```

If new samples have been added since the last analysis (compare `style.updated_at > last_analyzed_at`), show a nudge: "You've added samples since your last analysis. Re-analyze to update your voice profile."

**Note:** Store `analyzed_at` in the voice profile JSON returned by the analyze endpoint (already done in `pattern_extractor.py`'s `save_voice_profile` call stores a dict — just add `"analyzed_at"` to the `extract_voice_profile` tool's return schema).

---

### Phase 4: Onboarding Prompt

**Goal:** First-time users paste a writing sample before their first session. One-time, skippable.

#### `frontend/src/lib/components/OnboardingPrompt.svelte`

New component — shown on `/dashboard` when `onboarding_completed = false`:

```
"Let's learn your voice"

Paste something you've written — a blog post, essay, email, anything. Inkwell will use it
to match your voice from the first draft.

[ __________________________________________ ]
[ __________________________________________ ]  (textarea, ≥50 chars to enable submit)
[ __________________________________________ ]

[ Start with my voice ]       Skip for now →
```

On submit:
1. `styles.createStyle('My Writing', '')` → get `style.id`
2. `styles.addSample(style.id, 'My writing sample', content)`
3. `styles.analyzeStyle(style.id)` — fire and forget (don't await)
4. `POST /api/preferences/onboarding` — mark completed
5. Set `session.styleId = style.id` in the session store
6. Hide the onboarding prompt; TaskSelector appears with "My Writing" pre-selected

On skip:
1. `POST /api/preferences/onboarding` — mark completed (so it doesn't appear again)
2. TaskSelector appears with no style selected

#### `frontend/src/routes/(app)/dashboard/+page.server.ts`

Extend to return `onboardingCompleted` and `lastStyleId`:

```typescript
// Call GET /api/preferences alongside GET /api/sessions
const [sessions, prefs] = await Promise.all([
  fetch(`${INTERNAL_API_URL}/api/sessions`, { headers }),
  fetch(`${INTERNAL_API_URL}/api/preferences`, { headers }),
]);
return {
  sessions: await sessions.json(),
  onboardingCompleted: prefs.ok ? (await prefs.json()).onboarding_completed : false,
  lastStyleId: prefs.ok ? (await prefs.json()).last_style_id : null,
};
```

#### `frontend/src/routes/(app)/dashboard/+page.svelte`

```svelte
{#if session.screen === 'task'}
  {#if !data.onboardingCompleted}
    <OnboardingPrompt onComplete={(styleId) => { session.styleId = styleId; }} />
  {:else}
    <TaskSelector
      onResume={(id) => goto('/session/' + id)}
      defaultStyleId={data.lastStyleId}
    />
    <!-- recent sessions list -->
  {/if}
```

---

### Phase 5: Style Picker on TaskSelector + Session Store

**Goal:** Users pick a style before starting a session; `style_id` flows through to the backend.

#### `frontend/src/lib/stores/session.svelte.ts`

Add `styleId`:

```typescript
styleId = $state<number | null>(null);

startInterview(taskType: string, topic: string, styleId: number | null = null): void {
  this.taskType = taskType;
  this.topic = topic;
  this.styleId = styleId;
  this.messages = [];
  this.screen = 'interview';
}
```

#### `frontend/src/lib/ws.svelte.ts`

Update the `task.select` ClientMessage type (line 46):

```typescript
| { type: 'task.select'; task_type: string; topic: string; style_id?: number }
```

#### `frontend/src/lib/components/TaskSelector.svelte`

New props:

```typescript
let {
  onResume,
  defaultStyleId = null,
}: {
  onResume: (sessionId: number) => void;
  defaultStyleId?: number | null;
} = $props();
```

Add to script:
- `let selectedStyleId = $state<number | null>(defaultStyleId)` — initialised from prop
- Load styles on mount from the existing `styles` store (already loaded in Sidebar's onMount; no double-fetch needed since `styles.styles` is shared state)

**Style picker UI** — compact horizontal row above the task pills:

```
Writing as:  [ My Writing ▾ ]         (dropdown-style button)
             ↕ dropdown options: style names + "No style" option
```

If `styles.styles.length === 0`: show `[ + Add your voice ]` link that sets `session.appView = 'styles'` in the sidebar and navigates to `/styles`.

Update `startWriting()`:

```typescript
function startWriting() {
  if (!topic.trim()) return;
  session.startInterview(selectedType, topic.trim(), selectedStyleId);
  ws.send({
    type: 'task.select',
    task_type: selectedType,
    topic: topic.trim(),
    ...(selectedStyleId ? { style_id: selectedStyleId } : {}),
  });
}
```

#### Active style indicator

In `dashboard/+page.svelte`, show a small chip in the workflow screens (non-task) if `session.styleId` is set:

```svelte
{#if session.screen !== 'task' && session.styleId}
  <div class="style-chip">
    Writing as: {styles.styles.find(s => s.id === session.styleId)?.name ?? 'My Writing'}
  </div>
{/if}
```

---

### Phase 6: Post-Focus-Exit "Save to Profile" Banner

**Goal:** After focus mode, offer to save the finished piece back into a style profile.

#### `frontend/src/lib/components/FocusEditor.svelte`

Intercept the exit flow:

```typescript
let showSaveBanner = $state(false);
let pieceContent = $state('');

function handleBack() {
  // Capture content BEFORE leaving focus
  pieceContent = focus.content;
  ws.send({ type: 'focus.exit' });
  focus.leaveFocus();
  session.goToDrafts();
  // Show banner after transition (brief delay for animation)
  setTimeout(() => { showSaveBanner = true; }, 300);
}
```

**Banner component** (inline in FocusEditor or as `SaveToBanner.svelte`):

```
┌─────────────────────────────────────────────────────┐
│  Save this piece to your writing profile?           │
│  It'll help Inkwell match your voice next time.     │
│                                                     │
│  [ My Writing ▾ ]    [ Save ]    [ Not now ]        │
└─────────────────────────────────────────────────────┘
```

Positioned as a fixed bottom bar, dismissible. The style dropdown defaults to `session.styleId` if set, otherwise to the first available style.

On "Save":

```typescript
async function savePiece(styleId: number) {
  await styles.addSample(styleId, session.topic || 'Untitled piece', pieceContent);
  showSaveBanner = false;
}
```

The `addSample` call already exists in the store. No new backend endpoints needed — the finished piece is just added as another `StyleSample`.

On "Not now": dismiss banner, `showSaveBanner = false`.

**Do NOT show banner if `pieceContent` was never modified** — compare against the original draft content at focus entry (stored in `focus.content` before first edit, or compare word count). If identical to original AI-generated content, skip the banner silently to avoid polluting the style profile with AI text.

---

### Phase 7: Remove Personal inspo/ Files

**Goal:** Cold sessions get no examples rather than someone else's voice.

Delete from `inspo/`:
- `janan_ganesh_essay.md`
- `janan_ganesh_essay_pol.md`
- `learning_flywheel1.md`
- `learning_flywheel2.md`
- `learning_flywheel3.md`

Verify `format_examples_for_prompt([])` returns `""` (it does — the preamble only appends if there are examples). The orchestrator's `_load_examples_context()` will return `""` for sessions with no style, which is the correct "no examples" fallback.

---

## Acceptance Criteria

### Functional

- [ ] New user sees onboarding prompt on first dashboard visit; can paste a sample and skip
- [ ] Skipping onboarding marks the flag; prompt never shows again
- [ ] Style picker appears on TaskSelector when user has at least one style
- [ ] Style picker defaults to last-used style (persisted across sessions via backend Preference)
- [ ] Starting a session with a style sends `style_id` in `task.select`; drafts are voice-matched
- [ ] Starting a session with no style produces drafts with no injected style (no inspo/ fallback)
- [ ] StyleEditor shows tone pill selector, audience and domain text inputs; changes persist
- [ ] "Analyze my voice" button appears in StyleEditor; disabled with 0 samples
- [ ] Clicking Analyze shows loading state, then displays voice profile (descriptors, structure, strengths, weaknesses)
- [ ] "Re-analyze" button appears when new samples have been added since last analysis
- [ ] Academic and Technical tone → passive voice rule suppressed in focus mode
- [ ] Post-focus-exit banner appears when the piece was edited; hidden when content is unchanged from AI draft
- [ ] Banner style picker defaults to session style; selecting a style and saving adds a new StyleSample
- [ ] `npm run check` passes with no type errors
- [ ] All existing backend tests pass (`uv run pytest`)

### Non-Functional

- [ ] Analyze button disabled during in-flight request (no double-submit)
- [ ] `_analyze_cached` cache key includes suppressed rules (no stale cache hits across tones)
- [ ] inspo/ directory is empty; no personal writing samples remain as fallback

---

## File Change Summary

| File | Action | Notes |
|---|---|---|
| `backend/src/proof_editor/models/style.py` | Edit | Add `tone`, `audience`, `domain` fields |
| `backend/src/proof_editor/db.py` | Edit | Add `_migrate_schema()` with ALTER TABLE guards |
| `backend/src/proof_editor/api/styles.py` | Edit | Update PUT schema; include new fields in GET responses |
| `backend/src/proof_editor/api/preferences.py` | **New** | GET/POST endpoints for `onboarding_completed` + `last_style_id` |
| `backend/src/proof_editor/main.py` | Edit | Mount preferences router |
| `backend/src/proof_editor/learning/__init__.py` | Edit | Add `save_preference` / `load_preference` generic helpers |
| `backend/src/proof_editor/agent/orchestrator.py` | Edit | Write `last_style_id` pref on task.select; pass `tone` to FocusHandler |
| `backend/src/proof_editor/style/engine.py` | Edit | Add `suppressed` param + `get_suppressed_rules()`; fix cache key |
| `backend/src/proof_editor/agent/focus_handler.py` | Edit | Accept + pass `tone` to `engine.analyze()` |
| `inspo/` | **Delete all** | Remove personal writing samples |
| `frontend/src/lib/stores/styles.svelte.ts` | Edit | Add `VoiceProfile`, `analyzeStyle()`, `loadVoiceProfile()`, `voiceProfile`, `analyzing` |
| `frontend/src/lib/stores/session.svelte.ts` | Edit | Add `styleId`, thread through `startInterview()` |
| `frontend/src/lib/ws.svelte.ts` | Edit | Add `style_id?: number` to `task.select` ClientMessage |
| `frontend/src/lib/components/StyleEditor.svelte` | Edit | Add metadata fields, analyze button, voice profile display |
| `frontend/src/lib/components/TaskSelector.svelte` | Edit | Add style picker, pass `style_id` in WS send |
| `frontend/src/lib/components/OnboardingPrompt.svelte` | **New** | First-session onboarding component |
| `frontend/src/lib/components/FocusEditor.svelte` | Edit | Capture content on exit, show save-to-profile banner |
| `frontend/src/routes/(app)/dashboard/+page.server.ts` | Edit | Fetch preferences (onboarding flag + last style) |
| `frontend/src/routes/(app)/dashboard/+page.svelte` | Edit | Show OnboardingPrompt or TaskSelector; pass props |

---

## Dependencies & Risks

| Risk | Mitigation |
|---|---|
| SQLite ALTER TABLE fails on existing prod data | Use `inspect()` to check column existence before altering; guard each migration idempotently |
| Voice profile display in StyleEditor looks cluttered | Design profile as a collapsible section; collapsed by default if not yet analyzed |
| TaskSelector style picker adds visual weight before writing | Keep picker minimal — one line above the task pills, collapsed into a single button showing current style name |
| Banner appears every session even when the piece isn't personal | Compare `pieceContent !== originalDraftContent` before showing; skip silently if identical |
| `analyzeStyle()` is slow (LLM call, ~3-8s) | Show clear loading state + disable button during request |

---

## References

- Brainstorm: `docs/brainstorms/2026-02-20-styles-flywheel-brainstorm.md`
- Style engine: `backend/src/proof_editor/style/engine.py`
- Orchestrator style wiring: `backend/src/proof_editor/agent/orchestrator.py:218-249`
- Frontend WS types: `frontend/src/lib/ws.svelte.ts:46`
- Session store: `frontend/src/lib/stores/session.svelte.ts:44-55`
- StyleEditor current state: `frontend/src/lib/components/StyleEditor.svelte`
- Known SQLModel Literal bug: use `str` with app-level validation, never `Literal["a","b"]` in table columns
