# Backlog — Credit Card Spend Tracker MVP

## 1. Purpose

This backlog translates the PRD and the wireframes/schema/API spec into an implementation-ready work plan for engineering and Codex-driven development.

It is designed for the MVP only.

Core MVP scope:

* authentication
* cards management
* statement upload metadata
* transaction ingestion scaffolding
* transactions explorer
* categories and rules
* rewards ledger
* charges tracking
* dashboard analytics
* card detail analytics
* async statement-processing scaffold
* deterministic categorization scaffold

Out of scope for MVP:

* direct bank integrations
* email statement fetching
* advanced reward optimization engine
* full OCR-heavy parsing coverage across all issuers
* mobile app
* family/shared accounts
* reward redemption workflows

---

## 2. Prioritization Model

Priority labels:

* **P0** = required for MVP launch
* **P1** = important but can follow immediately after MVP core
* **P2** = post-MVP / hardening / enhancement

Status labels:

* **Not Started**
* **In Progress**
* **Blocked**
* **Done**

---

## 3. Milestones

### Milestone 1 — Foundation

Goal: repository, backend, DB, auth, and local development setup are working.

### Milestone 2 — Core Entities

Goal: cards, categories, and rules are fully manageable.

### Milestone 3 — Statement and Transaction Core

Goal: statements can be registered and transactions can be stored, queried, and edited.

### Milestone 4 — Rewards, Charges, and Analytics

Goal: card summaries and dashboard analytics are powered by real persisted data.

### Milestone 5 — Frontend MVP

Goal: users can complete the core flows from UI.

### Milestone 6 — Processing Scaffold

Goal: async processing, parser interfaces, and first categorization pipeline are in place.

---

# 4. Epic Backlog

## Epic A — Project Foundation

**Priority:** P0
**Goal:** Set up the base project so all future work builds on stable infrastructure.

### A1. Backend project scaffold

**Priority:** P0
**Status:** Not Started

**Description**
Create the base FastAPI project structure with clean module boundaries.

**Tasks**

* Create backend app structure
* Add config module
* Add API router registration
* Add healthcheck endpoint
* Add response envelope helpers
* Add dependency management files

**Acceptance Criteria**

* Backend starts locally
* `/api/v1/health` returns success
* Project structure supports extension into auth, cards, statements, transactions, rewards, dashboard

**Dependencies**

* None

---

### A2. Database and ORM setup

**Priority:** P0
**Status:** Not Started

**Description**
Set up PostgreSQL, SQLAlchemy 2.x, session handling, base model, and Alembic.

**Tasks**

* Configure PostgreSQL connection
* Add SQLAlchemy base and session
* Add timestamp mixin
* Add Alembic config
* Add initial migration baseline

**Acceptance Criteria**

* App connects to PostgreSQL
* Alembic migrations run successfully
* DB session dependency is reusable in routes/services

**Dependencies**

* A1

---

### A3. Docker and local dev setup

**Priority:** P0
**Status:** Not Started

**Description**
Provide a consistent local environment.

**Tasks**

* Add docker-compose for backend + postgres
* Add `.env.example`
* Add README local run instructions
* Add Makefile or task runner shortcuts if useful

**Acceptance Criteria**

* Local environment can be started with documented steps
* New developer can boot the app and DB without manual guesswork

**Dependencies**

* A1, A2

---

### A4. Test and quality tooling

**Priority:** P0
**Status:** Not Started

**Description**
Add basic quality controls.

**Tasks**

* Add pytest
* Add formatting and linting setup
* Add test DB strategy
* Add minimal smoke tests

**Acceptance Criteria**

* Tests run locally
* At least healthcheck and app boot tests pass

**Dependencies**

* A1, A2

---

## Epic B — Authentication and User Management

**Priority:** P0
**Goal:** Users can sign up, log in, and access only their own data.

### B1. User model and migration

**Priority:** P0
**Status:** Done

**Tasks**

* Add `users` model
* Add unique email constraint
* Add migration

**Acceptance Criteria**

* Users table exists with required fields
* Email uniqueness enforced

**Dependencies**

* A2

---

### B2. Password hashing and JWT auth

**Priority:** P0
**Status:** Done

**Tasks**

* Add password hashing utility
* Add JWT creation/verification
* Add auth settings from env
* Add current-user dependency

**Acceptance Criteria**

* Plain passwords are never stored
* Protected routes require valid token

**Dependencies**

* B1

---

### B3. Auth endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `POST /api/v1/auth/signup`
* `POST /api/v1/auth/login`
* `GET /api/v1/auth/me`

**Acceptance Criteria**

* Signup returns user + token
* Login returns token on valid credentials
* `/auth/me` returns current authenticated user
* Invalid credentials handled cleanly

**Dependencies**

* B2

---

### B4. Auth tests

**Priority:** P0
**Status:** Done

**Tasks**

* Add signup tests
* Add login tests
* Add invalid login tests
* Add protected route access tests

**Acceptance Criteria**

* Core auth flows are covered by automated tests

**Dependencies**

* B3

---

## Epic C — Cards Management

**Priority:** P0
**Goal:** Users can create and manage cards with reward and fee metadata.

### C1. Card model and migration

**Priority:** P0
**Status:** Done

**Tasks**

* Add `cards` model
* Add migration
* Add index on `(user_id, status)`

**Acceptance Criteria**

* Cards table supports all MVP metadata fields

**Dependencies**

* A2, B3

---

### C2. Card CRUD service layer

**Priority:** P0
**Status:** Done

**Tasks**

* Add create/list/get/update/archive service logic
* Enforce user ownership
* Validate `last4`

**Acceptance Criteria**

* Service layer supports all route operations cleanly

**Dependencies**

* C1

---

### C3. Card endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/cards`
* `POST /api/v1/cards`
* `GET /api/v1/cards/{card_id}`
* `PATCH /api/v1/cards/{card_id}`
* `DELETE /api/v1/cards/{card_id}`

**Acceptance Criteria**

* Cards can be created, edited, listed, and archived
* Users cannot access another user’s cards

**Dependencies**

* C2

---

### C4. Card CRUD tests

**Priority:** P0
**Status:** Done

**Acceptance Criteria**

* Happy path and ownership tests exist for all card endpoints

**Dependencies**

* C3

---

## Epic D — Categories and Rules

**Priority:** P0
**Goal:** Users can manage categories and reusable categorization rules.

### D1. Category model and migration

**Priority:** P0
**Status:** Done

### D2. Categorization rule model and migration

**Priority:** P0
**Status:** Done

### D3. Categories CRUD endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/categories`
* `POST /api/v1/categories`
* `PATCH /api/v1/categories/{category_id}`
* `DELETE /api/v1/categories/{category_id}`

**Acceptance Criteria**

* Support default and user-defined categories
* Soft archive supported
* Category `group_name` validated

**Dependencies**

* D1

---

### D4. Rules CRUD endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/rules`
* `POST /api/v1/rules`
* `PATCH /api/v1/rules/{rule_id}`
* `DELETE /api/v1/rules/{rule_id}`

**Acceptance Criteria**

* Rules can be enabled/disabled
* Rule category ownership/default validation enforced

**Dependencies**

* D2, D3

---

### D5. Categories and rules tests

**Priority:** P0
**Status:** Done

**Dependencies**

* D3, D4

---

## Epic E — Statement Upload Metadata

**Priority:** P0
**Goal:** Users can register uploaded statement files and track processing lifecycle.

### E1. Statement model and migration

**Priority:** P0
**Status:** Done

### E2. Upload storage abstraction

**Priority:** P0
**Status:** Done

**Tasks**

* Create storage interface
* Add dev/local fake implementation
* Keep S3-compatible path for later

**Dependencies**

* A1

---

### E3. Presign upload endpoint

**Priority:** P0
**Status:** Done

**Endpoint**

* `POST /api/v1/uploads/presign`

**Acceptance Criteria**

* Returns development upload target or presign-compatible response shape

**Dependencies**

* E2

---

### E4. Statements CRUD-lite endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `POST /api/v1/statements`
* `GET /api/v1/statements`
* `GET /api/v1/statements/{statement_id}`
* `POST /api/v1/statements/{statement_id}/retry`
* `DELETE /api/v1/statements/{statement_id}`

**Acceptance Criteria**

* Statements can be registered against owned cards
* Filters by card/status/month work
* Retry updates lifecycle correctly
* Delete behavior is clearly documented

**Dependencies**

* E1, E3, C3

---

### E5. Statement metadata tests

**Priority:** P0
**Status:** Done

**Dependencies**

* E4

---

## Epic F — Transactions and Audit Trail

**Priority:** P0
**Goal:** Transactions can be stored, queried, filtered, edited, and audited.

### F1. Transaction model and migration

**Priority:** P0
**Status:** Done

### F2. Category audit model and migration

**Priority:** P0
**Status:** Done

### F3. Transaction query service

**Priority:** P0
**Status:** Done

**Tasks**

* Filtering
* Sorting
* Pagination
* Ownership scoping
* Search by description/merchant

**Dependencies**

* F1

---

### F4. Transactions endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/transactions`
* `GET /api/v1/transactions/{transaction_id}`
* `PATCH /api/v1/transactions/{transaction_id}`
* `POST /api/v1/transactions/bulk-update`

**Acceptance Criteria**

* Supports documented filters and response meta
* Category updates create audit entries
* Optional rule creation supported on patch

**Dependencies**

* F2, F3, D4

---

### F5. Transactions tests

**Priority:** P0
**Status:** Done

**Dependencies**

* F4

---

## Epic G — Rewards and Charges

**Priority:** P0
**Goal:** Manual reward tracking and charge breakdown are available per card.

### G1. Reward ledger model and migration

**Priority:** P0
**Status:** Done

### G2. Card charge summary model and migration

**Priority:** P0
**Status:** Done

### G3. Reward ledger CRUD endpoints
**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/reward-ledgers`
* `POST /api/v1/reward-ledgers`
* `PATCH /api/v1/reward-ledgers/{reward_ledger_id}`
* `DELETE /api/v1/reward-ledgers/{reward_ledger_id}`

**Dependencies**

* G1

---

### G4. Card rewards and charges summary endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/cards/{card_id}/rewards`
* `GET /api/v1/cards/{card_id}/charges`

**Acceptance Criteria**

* Reward summary aggregates earned/redeemed/expired/value
* Charges summary returns structured breakdown

**Dependencies**

* G2, G3

---

### G5. Rewards and charges tests

**Priority:** P0
**Status:** Done

**Dependencies**

* G4

---

## Epic H — Dashboard and Card Analytics

**Priority:** P0
**Goal:** Users can understand spend, rewards, charges, and net value from analytics endpoints.

### H1. Dashboard aggregation query layer

**Priority:** P0
**Status:** Done

**Tasks**

* Build spend summary queries
* Build category/card aggregations
* Build monthly trend queries
* Build top merchant queries
* Build reward vs charges query

**Dependencies**

* F4, G4

---

### H2. Dashboard endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/dashboard/summary`
* `GET /api/v1/dashboard/spend-by-category`
* `GET /api/v1/dashboard/spend-by-card`
* `GET /api/v1/dashboard/rewards-vs-charges`
* `GET /api/v1/dashboard/monthly-trend`
* `GET /api/v1/dashboard/top-merchants`

**Acceptance Criteria**

* Duplicate transactions excluded from summaries
* Charges are distinguished from regular spend where required

**Dependencies**

* H1

---

### H3. Card analytics endpoints

**Priority:** P0
**Status:** Done

**Endpoints**

* `GET /api/v1/cards/{card_id}/summary`
* `GET /api/v1/cards/{card_id}/monthly-trend`
* `GET /api/v1/cards/{card_id}/transactions`

**Dependencies**

* H1

---

### H4. Dashboard analytics tests

**Priority:** P0
**Status:** Done

**Dependencies**

* H2, H3

---

## Epic I — Frontend MVP

**Priority:** P0
**Goal:** Implement the core UI and connect it to the backend.

### I1. Frontend app scaffold

**Priority:** P0
**Status:** Not Started

**Tasks**

* Next.js app setup
* Tailwind setup
* route structure
* API client setup
* auth-aware app shell

**Dependencies**

* B3

---

### I2. Shared components

**Priority:** P0
**Status:** Not Started

**Components**

* sidebar
* top filter bar
* KPI card
* chart card
* status pill
* upload dropzone
* transaction table
* category select

**Dependencies**

* I1

---

### I3. Auth and onboarding screens

**Priority:** P0
**Status:** Not Started

**Dependencies**

* I1, B3, C3

---

### I4. Dashboard screen

**Priority:** P0
**Status:** Not Started

**Dependencies**

* I2, H2

---

### I5. Cards list and card detail screens

**Priority:** P0
**Status:** Not Started

**Dependencies**

* I2, C3, H3, G4

---

### I6. Statement upload and history screens

**Priority:** P0
**Status:** Not Started

**Dependencies**

* I2, E4

---

### I7. Transactions explorer screen

**Priority:** P0
**Status:** Not Started

**Dependencies**

* I2, F4

---

### I8. Categories and rules screen

**Priority:** P0
**Status:** Not Started

**Dependencies**

* I2, D4

---

### I9. Settings screen

**Priority:** P1
**Status:** Not Started

**Dependencies**

* I1

---

### I10. Frontend integration and smoke tests

**Priority:** P0
**Status:** Not Started

**Dependencies**

* I4, I5, I6, I7, I8

---

## Epic J — Async Processing Scaffold

**Priority:** P1
**Goal:** Introduce background processing for statements without yet solving full parser coverage.

### J1. Worker setup

**Priority:** P1
**Status:** Not Started

**Tasks**

* Add worker app
* Add task queue integration
* Add local dev configuration

**Dependencies**

* E4

---

### J2. Statement processing job lifecycle

**Priority:** P1
**Status:** Not Started

**Tasks**

* Trigger on statement create/retry
* Update extraction/categorization statuses
* Handle success/failure/retry markers

**Dependencies**

* J1

---

### J3. Parser interface scaffold

**Priority:** P1
**Status:** Not Started

**Tasks**

* Define parser contract
* Add no-op/sample parser
* Return normalized placeholder output shape

**Dependencies**

* J2

---

### J4. Normalization interface scaffold

**Priority:** P1
**Status:** Not Started

**Dependencies**

* J3

---

### J5. Async pipeline tests

**Priority:** P1
**Status:** Not Started

**Dependencies**

* J4

---

## Epic K — Categorization Pipeline Scaffold

**Priority:** P1
**Goal:** Add the first deterministic categorization path and prepare for later LLM fallback.

### K1. Deterministic rule engine

**Priority:** P1
**Status:** Not Started

**Tasks**

* Apply user rules by priority
* Apply simple charge keyword mapping
* Persist category source and confidence

**Dependencies**

* D4, J4

---

### K2. Merchant-history matching scaffold

**Priority:** P1
**Status:** Not Started

**Dependencies**

* K1

---

### K3. LLM provider interface stub

**Priority:** P1
**Status:** Not Started

**Tasks**

* Define provider interface
* Do not make real calls yet
* Keep provider replaceable

**Dependencies**

* K2

---

### K4. Review queue behavior

**Priority:** P1
**Status:** Not Started

**Tasks**

* Mark low-confidence transactions with `review_required=true`
* Expose reviewable transactions via existing filters

**Dependencies**

* K1

---

### K5. Categorization tests

**Priority:** P1
**Status:** Not Started

**Dependencies**

* K4

---

## Epic L — Hardening and Developer Experience

**Priority:** P2
**Goal:** Improve maintainability, observability, and deployment readiness.

### L1. Repository/service refactor pass

**Priority:** P2
**Status:** Not Started

### L2. Error handling and logging standardization

**Priority:** P2
**Status:** Not Started

### L3. Seed data and demo fixtures

**Priority:** P2
**Status:** Not Started

### L4. CI setup

**Priority:** P2
**Status:** Not Started

### L5. API docs and onboarding docs refresh

**Priority:** P2
**Status:** Not Started

---

# 5. Suggested Sprint Plan

## Sprint 1

* A1 Backend project scaffold
* A2 Database and ORM setup
* A3 Docker and local dev setup
* A4 Test and quality tooling
* B1 User model and migration
* B2 Password hashing and JWT auth
* B3 Auth endpoints
* B4 Auth tests

## Sprint 2

* C1 Card model and migration
* C2 Card CRUD service layer
* C3 Card endpoints
* C4 Card tests
* D1 Category model and migration
* D2 Categorization rule model and migration
* D3 Categories CRUD endpoints
* D4 Rules CRUD endpoints
* D5 Categories and rules tests

## Sprint 3

* E1 Statement model and migration
* E2 Upload storage abstraction
* E3 Presign upload endpoint
* E4 Statements CRUD-lite endpoints
* E5 Statement metadata tests
* F1 Transaction model and migration
* F2 Category audit model and migration

## Sprint 4

* F3 Transaction query service
* F4 Transactions endpoints
* F5 Transactions tests
* G1 Reward ledger model and migration
* G2 Card charge summary model and migration
* G3 Reward ledger CRUD endpoints
* G4 Card rewards and charges summary endpoints
* G5 Rewards and charges tests

## Sprint 5

* H1 Dashboard aggregation query layer
* H2 Dashboard endpoints
* H3 Card analytics endpoints
* H4 Dashboard analytics tests
* I1 Frontend app scaffold
* I2 Shared components

## Sprint 6

* I3 Auth and onboarding screens
* I4 Dashboard screen
* I5 Cards list and card detail screens
* I6 Statement upload and history screens
* I7 Transactions explorer screen
* I8 Categories and rules screen
* I10 Frontend integration and smoke tests

## Sprint 7

* J1 Worker setup
* J2 Statement processing job lifecycle
* J3 Parser interface scaffold
* J4 Normalization interface scaffold
* J5 Async pipeline tests
* K1 Deterministic rule engine
* K2 Merchant-history matching scaffold
* K4 Review queue behavior
* K5 Categorization tests

## Sprint 8

* K3 LLM provider interface stub
* I9 Settings screen
* L1 Repository/service refactor pass
* L2 Error handling and logging standardization
* L3 Seed data and demo fixtures
* L4 CI setup
* L5 API docs and onboarding docs refresh

---

# 6. Codex Execution Notes

## How to use this backlog with Codex

For each backlog item:

1. create a focused branch
2. reference `docs/prd.md` and `docs/wireframes_schema_api.md`
3. ask Codex to implement one item or one tightly related cluster
4. require tests and docs updates
5. review the diff manually

## Recommended task granularity for Codex

Good:

* one model + migration + CRUD endpoint family
* one analytics module
* one screen
* one worker module

Bad:

* entire backend + frontend in one prompt
* all dashboard logic + async worker + categorization in one task

---

# 7. Definition of Done

A backlog item is considered done only if:

* code is implemented
* tests are added or updated
* migrations are included when schema changes
* docs/readme are updated when developer workflow changes
* route behavior matches the documented API contract
* ownership/security checks are in place where applicable

---

# 8. Immediate Next Items

If starting from scratch, do these first:

1. A1 Backend project scaffold
2. A2 Database and ORM setup
3. A3 Docker and local dev setup
4. B1 User model and migration
5. B2 Password hashing and JWT auth
6. B3 Auth endpoints

If backend foundation already exists, start here:

1. C1 Card model and migration
2. C2 Card CRUD service layer
3. C3 Card endpoints
4. D1 Category model and migration
5. D2 Categorization rule model and migration
6. D3 Categories CRUD endpoints
