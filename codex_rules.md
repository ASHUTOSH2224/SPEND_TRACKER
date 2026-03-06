# codex_rules.md

Use this file as the short operational ruleset for Codex on this project.

Read first:

* `AGENTS.md`
* `docs/prd.md`
* `docs/wireframes_schema_api.md`
* `docs/backlog.md`

If there is a conflict:

1. `docs/prd.md`
2. `docs/wireframes_schema_api.md`
3. `docs/backlog.md`
4. `AGENTS.md`
5. this file

---

## 1. Core behavior

* Stay within MVP unless explicitly asked otherwise.
* Make the smallest correct change.
* Do one bounded task at a time.
* Do not silently change architecture, API contracts, or schema.
* If something is ambiguous, choose the simplest implementation and state the assumption.

---

## 2. Repo rules

Top-level structure only:

```text
backend/
frontend/
infra/
docs/
prompts/
```

Do not:

* put business logic in `infra/`
* scatter docs outside `docs/`
* put deployment concerns in app code unless clearly necessary

---

## 3. Backend rules

Use this structure:

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

* routes thin
* business logic in `services/`
* aggregation/query logic in `queries/` or dedicated services
* SQLAlchemy models in `models/`
* Pydantic schemas in `schemas/`
* config/auth/shared app concerns in `core/`
* DB/session setup in `db/`
* background jobs in `workers/`

Never:

* put business logic in route handlers
* return raw exceptions to clients
* skip ownership checks
* store full card numbers

---

## 4. API rules

* All APIs under `/api/v1`
* Use the standard envelope:

```json
{
  "data": {},
  "meta": {},
  "error": null
}
```

* List endpoints must use consistent pagination
* Validate inputs explicitly
* Keep auth and ownership checks explicit
* Do not silently change response shapes

---

## 5. DB and migration rules

* Every model/schema change requires an Alembic migration
* Add indexes for common filters and joins
* Avoid N+1 queries
* Use SQL aggregation for dashboard metrics when possible
* Exclude `duplicate_flag=true` from summaries where required by spec

---

## 6. Frontend rules

* Follow wireframes before redesigning
* Reuse components
* Centralize API client code
* Keep forms typed and validation explicit
* Prefer simple state management
* Do not add unnecessary UI complexity in MVP

---

## 7. Async and AI rules

* Keep orchestration separate from parser/categorizer logic
* Status transitions must be explicit and persisted
* Deterministic rules before merchant history before LLM
* LLM only for ambiguous cases
* Persist `category_source`, `category_confidence`, `category_explanation`, `review_required`
* Store prompts in `prompts/`, not inline in service code

---

## 8. Performance rules

* Optimize for maintainability first, measured performance second
* Avoid repeated DB calls in loops
* Use pagination for large lists
* Avoid loading full datasets when SQL can aggregate
* Keep dashboards query-efficient

---

## 9. Security rules

* Never log secrets, tokens, or passwords
* Hash passwords
* Keep secrets in env vars or secret managers
* Treat statement files as sensitive financial data
* Enforce user ownership in backend queries

---

## 10. Testing rules

Every meaningful change must include tests.

Minimum expectations:

* route tests for new endpoints
* auth/ownership tests for protected behavior
* migration included for schema changes
* regression test for bug fixes

Do not finish a task without updating tests when behavior changes.

---

## 11. Documentation rules

Update docs when relevant:

* `README.md` for setup/run changes
* `docs/wireframes_schema_api.md` for API/schema changes
* `docs/backlog.md` if implementation order or scope changes materially

---

## 12. Output format for Codex

For implementation tasks, always respond with:

1. short plan
2. assumptions
3. file-by-file changes
4. migrations added/changed
5. tests added/changed
6. run/test commands
7. next recommended task

For refactor tasks:

1. short plan
2. files changed
3. behavior preserved
4. risks to review manually

---

## 13. Hard constraints

Do not:

* rewrite unrelated modules
* add large dependencies casually
* mix broad refactors with feature work unless asked
* hardcode fake analytics values into real code paths
* introduce hidden background behavior without visible status tracking
* call LLMs where deterministic logic is enough

---

## 14. Default implementation order

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
12. hardening
