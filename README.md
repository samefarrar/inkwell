# Inkwell

AI writing partner that interviews you, generates multiple draft angles, and refines based on your feedback.

## How It Works

1. **Specify a task** — essay, newsletter, landing page, review, etc.
2. **Interview** — the AI asks targeted questions one at a time to extract your real stories, insights, and experiences
3. **3 draft angles** — generates three drafts simultaneously, each taking a different angle on your material
4. **Highlight & refine** — mark what you like, flag what needs work, add custom labels. The AI synthesizes three new drafts from your feedback
5. **Iterate** — repeat the highlight/synthesize loop until you're satisfied

Every interaction compounds — highlights, edits, and style preferences feed back into future drafts.

## Stack

- **Backend**: Python 3.12 / FastAPI / LiteLLM / SQLite
- **Frontend**: Svelte 5 / SvelteKit / TipTap / Vite
- **Real-time**: WebSockets for interview chat and draft streaming

## Setup

### Backend

```bash
cd backend
uv sync
cp ../.env.example ../.env  # Add your API keys
```

### Frontend

```bash
cd frontend
npm install
```

### Run

```bash
./dev start    # Starts both servers
./dev stop     # Stops both
./dev status   # Check what's running
./dev logs     # Tail logs
```

Or run individually:

```bash
# Backend (port 8000)
cd backend && uv run python -m proof_editor

# Frontend (port 5173)
cd frontend && npm run dev
```

### Environment Variables

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCS_BUCKET_NAME=your-bucket
```

## Development

```bash
# Lint + format
cd backend && uv run ruff check --fix && uv run ruff format

# Type check
cd backend && uv run mypy src/

# Tests
cd backend && uv run --frozen pytest

# Svelte type check
cd frontend && npm run check
```
