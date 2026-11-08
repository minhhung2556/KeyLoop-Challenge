# Keyloop Challenge & `hei_projects` Leads Reference

This document caches requirements from `docs/challenge/challenge.md`, `docs/challenge/guide.md`, and the reference Leads implementation in `E:\projects\hooemi\hei_projects` so future tasks do not need to re-read source files.

---

## 1. Assessment Requirements Summary

- **Target Role:** Engineering Lead at Keyloop.
- **Submission Window:** Within 1 week (GitHub repo link + 5 to 10 minute video walkthrough link).
- **Selected Scenario:** **Scenario C: The Sales Lead Management Tool** (Domain: Demand).
- **Scenario Task:** Build a lightweight Sales Lead Management Tool to help dealership salespeople manage and track incoming leads from the dealership website.

### Core Acceptance Criteria (Scenario C)
1. **Lead Inbox:** Display a list of all incoming sales leads.
2. **Lead Details View:** Clicking a lead shows its full details and a chronological log of all follow-up activities.
3. **Activity Logging:** Provide an interface for a salesperson to log a new follow-up activity for a lead (for example "Called customer"), which must be persisted.

### Part 1: System Design Document Requirements
- Architecture diagram.
- Brief description of each component's role.
- Explanation of data flow (lead ingestion, inbox query, detail view, activity persistence).
- Chosen technologies with justifications.
- Strategy for observability (structured logging, metrics, distributed tracing).
- Dedicated section describing how GenAI assisted in the design phase, plus documented assumptions for any ambiguous requirements.

### Part 2: Service Implementation Requirements
- Implement either Backend (RESTful API + persistent database + client stub/OpenAPI/test harness) or Frontend (web app demonstrating full UX + mock/local persistent API), or both.
- Design for scalability, performance, reliability, maintainability, and observability.
- Include `README.md` with build, run, and test instructions.
- Include a dedicated **AI Collaboration Narrative** in `README.md` covering high-level prompting strategy, verification/refinement workflow, and quality assurance.
- Include automated tests validating core business logic.

### Evaluation Dimensions
1. **Problem Solving & System Design:** Clarity, logic, and foresight of architecture.
2. **Technical Execution:** Quality, correctness, and testing of implementation.
3. **AI Engineering & Verification:** Strategy for directing AI and verifying, debugging, and owning the final solution.
4. **Communication & Presentation:** Clarity and professionalism of documentation and 5 to 10 minute video.

---

## 2. Reference Implementation Inventory (`E:\projects\hooemi\hei_projects`)

### Backend (`hei_backend`)
- **Schemas (`hei_backend/app/schemas/lead.py`):**
  - `LeadStatus(str, Enum)`: `NEW = "new"`, `CONTACTED = "contacted"`, `CLOSED = "closed"`.
  - `LeadCreate`: `name` (1..200, stripped), `email` (`EmailStr`, lowercased), `phone` (normalized via `re.sub(r"[\s\-().]", "", val)`, validated with `^\+?[0-9]{8,20}$`), `message` (20..2000 chars, stripped), optional attribution (`utmSource`, `utmMedium`, `utmCampaign`, `utmContent`, `utmTerm`, `ref`, max 200 chars).
  - `LeadStatusUpdate`: `status: LeadStatus`.
  - `LeadResponse`: `id`, `name`, `email`, `phone`, `message`, `createdAt`, `status`, attribution fields.
  - `LeadListResponse`: `items: List[LeadResponse]`, `total: int`, `limit: int`, `offset: int`.
  - `LeadGrowthPoint` & `LeadGrowthResponse`: Daily cumulative series (`days: Literal[7, 30, 90]`, `date`, `total`, `new`, `contacted`, `closed`).
- **Service (`hei_backend/app/services/lead_service.py`):**
  - `create_lead(payload)`: Normalizes fields, sets `status = LeadStatus.NEW.value` and `createdAt = utcnow()`, persists document.
  - `list_leads_for_owner(owner_user_id, limit=50, offset=0, status=None, q=None)`: Sorts by `createdAt` desc, filters by `status` and casefolded substring `q` across contact/message/attribution fields, returns paginated slice + `total`.
  - `update_lead_status_for_owner(lead_id, owner_user_id, payload)`: Validates existence and ownership, updates `status`.
  - `lead_growth_points_from_created_dates(entries, days, today)`: Pure function computing daily cumulative counts across baseline and window dates.
- **Router (`hei_backend/app/api/v1/leads.py`):**
  - `POST /api/v1/leads` (201 Created)
  - `GET /api/v1/leads/mine` (200 OK, query params `limit`, `offset`, `status`, `q`)
  - `GET /api/v1/leads/mine/growth` (200 OK, query param `days` in 7, 30, 90)
  - `PATCH /api/v1/leads/{lead_id}` (200 OK)
- **Tests (`hei_backend/app/tests/test_api_leads.py`):**
  - Covers valid creation, phone normalization, email/phone/message 422 validation errors, attribution persistence, pagination, status filtering, search query, status update, and cumulative growth series math.

### Frontend (`hei_frontend`)
- **Hooks (`hei_frontend/src/hooks/`):**
  - `useMyLeads.ts`: TanStack `useInfiniteQuery` with `LEAD_LIST_PAGE_SIZE = 20`, `flattenLeadListPages`, keyed by `status` and `q`.
  - `useUpdateLeadStatus.ts`: `useMutation` calling `PATCH /leads/{leadId}` and invalidating `queryKeys.leads.all`.
  - `useLeadStatusCounts.ts`: Parallel count queries for `all`, `new`, `contacted`, `closed`.
  - `useLeadGrowth.ts`: `useQuery` for 7/30/90 day growth chart.
- **Components & Pages:**
  - `src/pages/dashboard/leads.tsx`: Inbox page with search bar, status filter pills, skeleton loading state, error retry panel, empty state (filtered vs unfiltered), lead cards with attribution chips, and status selector.
  - `src/components/dashboard/LeadStatusMenu.tsx`: Accessible listbox dropdown (`aria-haspopup="listbox"`, `aria-expanded`, spinner while mutating) with semantic badge colors (`new` = info, `contacted` = warning, `closed` = muted).
  - `src/components/dashboard/LeadOverviewMetricCards.tsx` & `LeadStatusOverviewChart.tsx`: Bento metric cards + Recharts responsive line chart.
  - `src/components/landing/LeadFormSection.tsx`: Public lead capture form with client-side field validation and phone normalization.

---

## 3. Gap Analysis: Adapting `hei_projects` Leads to Keyloop Scenario C

| Capability | `hei_projects` Status | Keyloop Scenario C Addition |
|---|---|---|
| Lead Inbox list, search, status filter, status badge | Implemented | Add automotive fields (`vehicleInterest`, `inquiryType`, `source`) and selection state |
| Lead KPIs & status workflow (`new`, `contacted`, `closed` / `qualified`) | Implemented | Keep status workflow and KPI cards |
| Clicking a lead opens Lead Details View | Missing (cards are inline only) | Add interactive Lead Details panel/view showing full customer, vehicle, attribution, and timestamps |
| Chronological follow-up activity log | Missing | Add `activities` collection/table and timeline UI ordered chronologically |
| Log new follow-up activity (persisted) | Missing | Add `POST /api/v1/leads/{id}/activities` + activity form (type: Call, Email, SMS, Test Drive, Note; summary; notes; author) |
