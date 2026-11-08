# Implementation Plan (Local Dev Only)

Follow this checklist in order. Do not add unapproved dependencies or production deploy configs.

## Guardrails

- Local only: FastAPI `127.0.0.1:8000` (`/docs` on), Next.js `127.0.0.1:3000`, SQLite `backend/leads.db`.
- Scope: Lead Inbox, Lead Detail + chronological activities, persist follow-up activity.
- Ask before any extra feature or library.

## Phase 1

- [x] 1.1 `docs/challenge/implementation-plan.md` + `AGENTS.md`
- [x] 1.2 `.cursor/rules/*.mdc`
- [x] 1.3 skills + `scripts/common.py` + `scripts/verify.py` + `scripts/bootstrap_from_hei.py`
- [x] 1.4 `docs/system-design.md`
- [x] 1.5 backend scaffold

## Phase 2

- [x] 2.1 schemas + SQLite repo + seed
- [x] 2.2 LeadService + router + `main.py`
- [x] 2.3 pytest (`scripts/verify.py --backend`)
- [x] 2.4 frontend scaffold + hooks
- [x] 2.5 Inbox / Detail / Activity UI
- [x] 2.6 frontend unit tests (`scripts/verify.py --frontend`)

## Phase 3

- [x] 3.1 `README.md` + `scripts/dev.py`
- [x] 3.2 HyperFrames + edge-tts + FFmpeg walkthrough
