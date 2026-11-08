# Keyloop Challenge Agent Context

Read this file first. Session tracker: `docs/challenge/implementation-plan.md`. Cached requirements: `docs/challenge/context-summary.md`.

## Guardrails (Composer)

- Local development only (`127.0.0.1:8000`, `127.0.0.1:3000`, SQLite `backend/leads.db`).
- Do not add unapproved libraries, endpoints, or production deploy files.
- Inspect files before editing. Atomic 2 to 4 file batches. Run `python scripts/verify.py` before finishing a step.
- If a requirement is ambiguous, stop and ask.

## Scenario C (strict)

1. Lead Inbox: list, search `q`, status filter `all|new|contacted|closed`.
2. Lead Details: full lead + chronological activities (`createdAt` ASC).
3. Activity logging: persist follow-up (`POST /api/v1/leads/{id}/activities`).

## Rule routing

| Work | Read |
|------|------|
| Any turn | `.cursor/rules/composer-execution.mdc` |
| `backend/**/*.py` | `.cursor/rules/backend-fastapi.mdc` |
| `frontend/**/*.{ts,tsx,css,js,mjs}` | `.cursor/rules/frontend-nextjs-tokens.mdc` |
| `video/**`, `scripts/build_walkthrough_video.py` | `.cursor/rules/hyperframes-video.mdc` |

Skills: `.cursor/skills/phase-runner`, `test-all`, `walkthrough-video`.

## Logging (hei_projects)

- `RequestIDMiddleware` + PII-masked `RequestLoggingMiddleware`.
- Critical path only: `lead_created`, `lead_status_updated`, `lead_activity_logged`, `db_operation_failed`.
- Errors: `{"detail": {"error_code", "message"}, "request_id"}`.
- CLI: `scripts/common.py` (`CheckResult`, `  ✅` / `  ❌`).
