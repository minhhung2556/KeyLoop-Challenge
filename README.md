# Keyloop Sales Lead Management Tool

Local-only Scenario C slice: website sales lead inbox, lead detail, and persisted follow-up activities.

## Stack

- Backend: FastAPI + Pydantic v2 + SQLite (`backend/leads.db`) on `127.0.0.1:8000` (`/docs` enabled)
- Frontend: Next.js Pages Router + TanStack Query + Tailwind on `127.0.0.1:3000`
- Primary token: `.bg-blue-20` / `#00B5D8`

## Setup

```powershell
python -m pip install -r backend/requirements.txt
npm --prefix frontend install
```

## Run (local)

```powershell
python scripts/dev.py
```

Or two terminals:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:3000` and `http://127.0.0.1:8000/docs`.

## Tests

```powershell
python scripts/verify.py --backend
python scripts/verify.py --frontend
python scripts/verify.py --all
```

## cURL examples

```powershell
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/api/v1/leads?q=Porsche"
curl http://127.0.0.1:8000/api/v1/leads/<lead_id>
curl -X POST http://127.0.0.1:8000/api/v1/leads/<lead_id>/activities -H "Content-Type: application/json" -d "{\"type\":\"call\",\"summary\":\"Called customer\"}"
```

First `call` or `email` on a `new` lead transitions status to `contacted`.

## AI Collaboration Narrative

Direction: freeze scope to inbox, detail, and persist activity. Reuse lead schemas, logging middleware, status menu, and design tokens in this slice. Walkthrough uses VieNeu-TTS-v3-Turbo (`Adam`) plus FFmpeg. Composer 2.5 executed atomic file batches with `scripts/verify.py` after each layer.

Verification: pytest covers 201/422/404, chronological activities, and auto status transition. Frontend `node:test` covers phone, attribution, error mapping, and activity sort. Typecheck runs via `npm run typecheck`.

Quality: Pydantic `extra="forbid"`, parameterized SQL, PII-masked request logging, `X-Request-ID` on errors, no production deploy configs.

## Video

```powershell
python scripts/build_walkthrough_video.py
```

Output: `video/output/keyloop_walkthrough.mp4`. Voice: VieNeu preset `Adam`. Visuals: live `127.0.0.1:3000` / `:8000/docs` screenshots. Transcript: `docs/video-walkthrough-script.md`.
