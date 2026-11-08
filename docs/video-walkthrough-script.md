# Video walkthrough transcript

English narration. VieNeu-TTS-v3-Turbo (`vieneu`, mode `v3turbo`, preset `Adam`). Visuals are live website screenshots plus architecture cards. Chapter `lines` are voiceover only, not on-screen transcript. Target length is at least five minutes. Chapters do not repeat the same beat.

## 1. Intro and Scenario C

Domain Demand: website inquiries already captured. Salesperson triages, opens context, writes a follow-up trail. Clone-and-run slice on `127.0.0.1:8000` / `:3000` / `leads.db`. No cloud, no extra KPI dashboard.

## 2. System design

Router, LeadService, SQLite WAL. Pydantic `extra="forbid"`. Two tables. Inbox newest-first with `q` and status. Detail activities ASC. Error envelope plus `X-Request-ID`. PII-masked request logs. Critical-path structlog only.

## 3. AI collaboration

Frozen plan and Cursor rules. Two-to-four file batches. `scripts/verify.py` after each batch. pytest, frontend node tests, typecheck. No extra libraries or metrics endpoint.

## 4. Application demo

Inbox newest-first. Filter New. Search Porsche. Open Lan Nguyen. Save Called customer. Status becomes contacted. OpenAPI `/docs` shows the five lead operations.

## 5. Lessons learned

Persist the plan. Gate on verify. One log dialect. Local SQLite, uvicorn, and next dev only.
