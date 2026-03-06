# AGENTS.md — Codex Project Rules

This file defines the working rules Codex must follow for this project.

These rules exist to preserve:

* clean project structure
* predictable architecture
* code quality
* performance and maintainability
* security and privacy
* consistency with the PRD and API/schema documents

Codex must read this file before making changes.

---

# 1. Source of Truth

Before making any change, read these files first:

* `docs/prd.md`
* `docs/wireframes_schema_api.md`
* `docs/backlog.md`

Rules:

* Do not invent features outside the documented MVP unless explicitly asked.
* If the spec is ambiguous, choose the simplest implementation that preserves the documented API contract.
* When making an assumption, state it clearly in the output.
* Do not silently drift away from the documented schema, routes, or user flows.

---

# 2. General Working Rules

* Make the smallest correct change that solves the task.
* Preserve existing architecture unless refactor is explicitly requested.
* Prefer incremental implementation over broad rewrites.
* Keep code easy for a human engineer to extend.
* Do not mix unrelated concerns in one change.
* Do not add hidden magic, implicit behavior, or unnecessary abstractions.
* Do not leave dead code, commented-out code, or placeholder hacks without marking them clearly.
* If a task requires schema changes, include migration changes in the same task.
* If a task changes API behavior, update tests and docs in the same task.

---

# 3. Repository Structure Rules

## 3.1 Allowed top-level structure

```text
backend/
frontend/
infra/
docs/
prompts/
```

### backend/

Contains backend application code only.

### frontend/

Contains frontend application code only.

### infra/

Contains deployment, Docker, Terraform, scripts, and runtime infrastructure only.

### docs/

Contains PRD, wireframes, API docs, backlog, architecture notes.

### prompts/

Contains prompt templates and LLM prompt assets.

Rules:

* Do not place app business logic inside `infra/`.
* Do not place deployment scripts inside `backend/` or `frontend/` unless they are truly app-local.
* Do not scatter docs across the repo.
* Keep generated files out of source directories unless intentionally committed.

---

# 4. Backend Rules

## 4.1 Backend architecture

Backend should be organized with clear boundaries:

```text
backend/app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  queries/
  workers/
  utils/
```

Rules:

* Route files must stay thin.
* Business logic belongs in `services/`.
* Query-heavy aggregation logic belongs in `queries/` or dedicated service modules.
* ORM models belong in `models/`.
* Pydantic request/response schemas belong in `schemas/`.
* Config, auth helpers, and shared app concerns belong in `core/`.
* DB setup, session handling, and migrations integration belong in `db/`.
* Background jobs belong in `workers/`.

## 4.2 API rules

* All endpoints must follow the documented `/api/v1` structure.
* Use the standard response envelope:

  * `data`
  * `meta`
  * `error`
* Validate input explicitly.
* Return structured errors, not raw exceptions.
* Keep auth and ownership checks explicit.
* Do not leak internal stack traces in API responses.
* Keep pagination consistent across list endpoints.

## 4.3 Model and schema rules

* Use UUID primary keys.
* Use explicit field types.
* Keep money fields consistent across the codebase.
* Never store full card number.
* Keep audit-related fields intact.
* Use enums or constrained values where appropriate, but avoid overcomplicating migrations.

## 4.4 Database rules

* Every schema change must include an Alembic migration.
* Do not modify production tables without migration support.
* Add indexes for frequently queried filters and joins.
* Avoid N+1 query patterns.
* Prefer explicit joins and query composition over implicit ORM behavior when performance matters.
* Dashboard queries must exclude duplicate transactions where required by spec.

## 4.5 Service rules

* Services should be deterministic and testable.
* Do not put request/response formatting inside services.
* Do not make services depend directly on framework-specific request objects.
* Keep side effects explicit.

---

# 5. Frontend Rules

## 5.1 Frontend architecture

Frontend should follow a predictable structure, for example:

```text
frontend/
  app/ or src/
  components/
  lib/
  hooks/
  types/
  styles/
```

Rules:

* Shared UI goes in reusable components.
* Page-specific composition stays at the page level.
* API client code must be centralized.
* Avoid duplicating request logic across pages.
* Keep form validation explicit.
* Use typed interfaces aligned with backend contracts.

## 5.2 UI rules

* Follow the wireframes before adding visual enhancements.
* Prioritize clarity over decoration.
* Keep dashboard information dense but readable.
* Use reusable filter bars, tables, KPI cards, and status pills.
* Do not overdesign early MVP screens.
* Avoid deeply nested state where simpler composition works.

## 5.3 State management rules

* Prefer local/component state first.
* Introduce global state only when clearly necessary.
* Server data fetching should use one consistent pattern.
* Cache and invalidation behavior should be explicit.

---

# 6. Async Processing and AI Pipeline Rules

## 6.1 Processing pipeline rules

* Keep orchestration separate from parsing and categorization logic.
* Statement processing stages must be explicit:

  * upload
  * extraction
  * normalization
  * categorization
  * completion/failure
* Status transitions must be persisted.
* Failures must be visible and retryable.

## 6.2 Parser rules

* Do not hardcode bank-specific parsing into general pipeline modules.
* Use parser interfaces and issuer-specific implementations.
* Preserve raw extracted data in metadata where useful for audit/debugging.

## 6.3 Categorization rules

* Deterministic rules must run before any LLM step.
* Merchant/history matching must run before LLM fallback.
* LLM should only be used for ambiguous or unmatched cases.
* Persist:

  * category source
  * confidence
  * explanation
  * review flag
* Do not let LLM override strong deterministic matches unless explicitly designed.

## 6.4 Prompt rules

* Store prompts under `prompts/`.
* Keep prompts versionable and readable.
* Do not hardcode long prompts inline in business logic files.
* Prompt templates must be easy to test and replace.

---

# 7. Performance and Optimization Rules

## 7.1 General optimization

* Optimize for maintainability first, then measured performance.
* Do not micro-optimize early without evidence.
* Avoid unnecessary abstraction layers.
* Prefer simple, index-friendly query patterns.
* Batch DB work where appropriate.
* Avoid repeated DB calls in loops.
* Use pagination for list views and APIs.

## 7.2 Backend performance

* Dashboard aggregations must be computed efficiently.
* Avoid loading full datasets into memory when aggregation can be done in SQL.
* Avoid unnecessary JSON serialization/deserialization in hot paths.
* Keep transaction update flows efficient and audit-safe.
* Use proper indexes for common transaction filters.

## 7.3 Frontend performance

* Avoid over-fetching.
* Use pagination and lazy loading where helpful.
* Keep charts and large tables efficient.
* Do not block initial page render on non-critical data.

---

# 8. Security and Privacy Rules

* Never store full card numbers.
* Never log secrets, passwords, or raw tokens.
* Passwords must be hashed.
* Auth secrets must come from environment variables or secret managers.
* Enforce ownership checks at the backend.
* Uploaded statements must be treated as sensitive financial data.
* Storage paths and access controls must be designed with privacy in mind.
* Do not expose internal IDs or internal errors carelessly.

---

# 9. Testing Rules

* Every behavior change must include tests or updated tests.
* Add unit tests for service logic where practical.
* Add API tests for route behavior, auth, validation, and ownership.
* Add query/aggregation tests for dashboard logic.
* Add regression tests when fixing bugs.
* Prefer small deterministic fixtures over brittle test setups.

Rules:

* Do not merge endpoint work without at least basic happy-path and auth/ownership coverage.
* Do not change schema behavior without migration and test updates.

---

# 10. Migration Rules

* Every model change requires an Alembic migration.
* Migration names must be descriptive.
* Do not hand-edit tables in ways that diverge from ORM definitions without documenting why.
* If a migration is risky or destructive, call it out clearly.

---

# 11. Logging and Error Handling Rules

* Use consistent structured logging.
* Log important lifecycle events for statement processing.
* Log failures with enough context for debugging, but never include secrets or sensitive raw financial data unnecessarily.
* Use consistent error codes for API responses.
* Prefer explicit application errors over generic exceptions.

---

# 12. Documentation Rules

When changing important behavior, update the relevant docs:

* `docs/prd.md` if scope or product behavior changes
* `docs/wireframes_schema_api.md` if schema or contract changes
* `docs/backlog.md` if implementation order or major status changes
* `README.md` if setup or run workflow changes

Rules:

* Keep docs close to reality.
* Do not leave architecture drift undocumented.

---

# 13. Codex Output Format Rules

For implementation tasks, Codex should respond with:

1. short plan
2. assumptions
3. file-by-file changes
4. migrations added or changed
5. tests added or changed
6. run/test commands
7. next recommended task

For refactor tasks, Codex should respond with:

1. short plan
2. files changed
3. behavior preserved
4. risks to review manually

---

# 14. What Codex Must Not Do

* Do not rewrite large parts of the repo unless explicitly asked.
* Do not invent new architecture layers without justification.
* Do not add dependencies casually.
* Do not mix formatting-only churn with business changes unless requested.
* Do not bypass auth, ownership, or audit requirements for convenience.
* Do not put business logic into route handlers.
* Do not hardcode sample values in real dashboard calculations.
* Do not silently change API contracts.
* Do not add LLM calls where deterministic logic is sufficient.
* Do not create hidden background behavior without visible status tracking.

---

# 15. Preferred Implementation Order

Unless explicitly told otherwise, follow this order:

1. foundation
2. auth
3. cards
4. categories and rules
5. statements metadata
6. transactions and audit
7. rewards and charges
8. dashboard analytics
9. frontend MVP
10. async processing scaffold
11. categorization pipeline
12. hardening and refactor pass

---

# 16. Final Rule

If a requested change conflicts with this file, the PRD, or the API/schema spec:

* call out the conflict explicitly
* implement the safest minimal change
* do not silently choose a divergent direction
