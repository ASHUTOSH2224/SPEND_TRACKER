# Spend Tracker

Foundation scaffold for the credit-card spend tracking backend described in `docs/`.

## Current scope

This milestone implements backend foundation plus the first protected MVP entities:
- FastAPI application scaffold
- environment-driven configuration
- PostgreSQL-ready SQLAlchemy 2.x session management
- Alembic migration setup
- reusable base model and timestamp mixins
- healthcheck endpoint at `/api/v1/health`
- local email/password authentication with JWT bearer tokens
- authenticated cards CRUD with soft archive behavior
- local-development upload presign support backed by on-disk statement files
- authenticated statement metadata create/list/detail/retry/delete endpoints
- async statement-processing scaffold with a polling worker and queued jobs
- transaction explorer list/detail/update/bulk-update APIs
- transaction category audit logging for manual recategorization
- reward ledger CRUD APIs for manual reward entries
- card rewards and persisted charge summary endpoints
- dashboard analytics and card performance endpoints backed by SQL aggregations
- Next.js frontend MVP shell with authenticated dashboard, cards, uploads, transactions, categories, statements, and settings routes
- Docker compose support for backend plus PostgreSQL
- pytest smoke coverage

The async scaffold now queues statement-processing jobs and persists explicit
status transitions. Bank-specific parsing and real LLM categorization are still
deferred beyond the first narrow importer. The current worker supports two real
HDFC formats:
- `HDFC + CSV`, using the columns `Transaction Date`, `Post Date`, `Description`, `Debit`, `Credit`, `Currency`, and optional `Merchant`
- `HDFC + PDF` statements whose text layer exposes `Domestic Transactions` rows like `DD/MM/YYYY| HH:MM ... C 1,234.56`

Other issuers and file formats still fall back to the no-op parser. Unsupported
HDFC PDFs now fail extraction explicitly instead of completing with zero imported
transactions. The worker also uses a default
normalizer, a deterministic categorization scaffold, a merchant-history hook,
and a no-op LLM provider stub.

## Repository layout

```text
backend/
frontend/
infra/
docs/
prompts/
```

Backend application code lives under `backend/app/` with these module boundaries:

```text
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

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose, if using the container workflow

## Local environment

1. Create a local environment file from the template.
2. Set either `DATABASE_URL` directly or the individual `POSTGRES_*` variables.
3. Set `AUTH_SECRET_KEY` for JWT signing. The checked-in default is for local development only.
4. Set `STATEMENT_SECRET_KEY` for encrypting PDF passwords at rest. If unset, the backend falls back to `AUTH_SECRET_KEY` in local development.
5. Set `STORAGE_BACKEND=local_fake` unless you are wiring a different storage adapter.
6. `STORAGE_LOCAL_ROOT` controls where local-development statement files are written. Relative values are resolved from the repo root so the API server and worker use the same folder even if they start from different directories. The default is `.local_storage/` at the repo root.
7. Worker defaults are `WORKER_POLL_INTERVAL_SECONDS=5`, `WORKER_BATCH_SIZE=10`, and `LLM_PROVIDER_BACKEND=noop`.
8. The default template uses `localhost:5433` so the Dockerized PostgreSQL service does not collide with an existing local PostgreSQL server on `5432`.
9. Docker Compose overrides the backend container to use the internal database host `postgres:5432`.
10. In Docker, the `api` and `worker` services must share the same statement storage volume. The checked-in Compose file now mounts a shared `statement_storage` volume at `/app/.local_storage` for both services.

Example:

```bash
cp .env.example .env
```

## Run locally with a virtual environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API docs will be available at `http://127.0.0.1:8000/docs`.

Run the local worker in a second terminal:

```bash
cd backend
source .venv/bin/activate
python -m app.workers.statement_worker
```

Auth endpoints:

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Card endpoints:

- `GET /api/v1/cards`
- `POST /api/v1/cards`
- `GET /api/v1/cards/{card_id}`
- `PATCH /api/v1/cards/{card_id}`
- `DELETE /api/v1/cards/{card_id}`

Upload and statement metadata endpoints:

- `POST /api/v1/uploads/presign`
- `POST /api/v1/statements`
- `GET /api/v1/statements`
- `GET /api/v1/statements/{statement_id}`
- `POST /api/v1/statements/{statement_id}/retry`
- `DELETE /api/v1/statements/{statement_id}`

Statement processing scaffold behavior:

- `POST /api/v1/statements` and `POST /api/v1/statements/{statement_id}/retry` enqueue a `statement_processing_jobs` row.
- `POST /api/v1/uploads/presign` returns a local-development `upload_url` that accepts a `PUT` to write the statement file under `STORAGE_LOCAL_ROOT`.
- `POST /api/v1/statements` requires `file_password` for `file_type=pdf`. The password is stored encrypted at rest and is not returned by statement read/list responses.
- The worker updates statement statuses through `uploaded/pending/pending -> processing/running/pending -> processing/completed/running -> completed/completed/completed` on success.
- Extraction failures mark statements `failed/failed/pending`.
- Categorization failures mark statements `failed/completed/failed`.
- Real parser coverage now includes:
  - `HDFC + CSV` with headers `Transaction Date`, `Post Date`, `Description`, `Debit`, `Credit`, `Currency`, and optional `Merchant`
  - `HDFC + PDF` statements whose text layer exposes `Domestic Transactions` rows like `DD/MM/YYYY| HH:MM ... C 1,234.56`
- Imported rows preserve raw parser metadata under each transaction's `metadata_json.raw_metadata`.
- Credit bill repayments such as `CC PAYMENT`, `BILL PAYMENT`, `BILLDESK`, `NEFT`, or `IMPS` are stored as `txn_type=payment`, while cancelled or reversed merchant credits remain `txn_type=refund`.
- Unsupported HDFC PDFs fail extraction explicitly, while unsupported other formats still fall back to the no-op parser.
- On worker startup, older `completed + 0 transaction` statements are re-queued once with trigger source `parser_backfill` when a real parser now exists for that issuer/file-type combination.
- The worker now reads the stored statement file by `file_storage_key` before invoking the parser, and passes the decrypted PDF password to issuer-specific parsers when present.

Transaction endpoints:

- `GET /api/v1/transactions`
- `GET /api/v1/transactions/{transaction_id}`
- `PATCH /api/v1/transactions/{transaction_id}`
- `POST /api/v1/transactions/bulk-update`

Reward endpoints:

- `GET /api/v1/reward-ledgers`
- `POST /api/v1/reward-ledgers`
- `PATCH /api/v1/reward-ledgers/{reward_ledger_id}`
- `DELETE /api/v1/reward-ledgers/{reward_ledger_id}`
- `GET /api/v1/cards/{card_id}/rewards`
- `GET /api/v1/cards/{card_id}/charges`

Dashboard and card analytics endpoints:

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/spend-by-category`
- `GET /api/v1/dashboard/spend-by-card`
- `GET /api/v1/dashboard/rewards-vs-charges`
- `GET /api/v1/dashboard/monthly-trend`
- `GET /api/v1/dashboard/top-merchants`
- `GET /api/v1/cards/{card_id}/summary`
- `GET /api/v1/cards/{card_id}/monthly-trend`
- `GET /api/v1/cards/{card_id}/transactions`

Statement delete policy for the current MVP slice:

- `DELETE /api/v1/statements/{statement_id}` is blocked if the statement already has linked transactions.
- If a statement has no linked transactions, the route removes the statement metadata row and any queued or historical processing jobs for that statement.
- The local development storage backend deletes the stored file when it exists.

Charge summary source for the current MVP slice:

- `card_charge_summaries` are derived rows rebuilt from imported transactions where `statement_id` is present, `is_card_charge=true`, and `duplicate_flag=false`.
- Charge totals use explicit signed import rules: debit charge rows add to the month total, while credit charge rows subtract from it.
- `GET /api/v1/cards/{card_id}/charges` reads persisted rows from `card_charge_summaries`.
- The response exposes `source=card_charge_summaries` and `summary_period_count` so the provenance is explicit.
- `GET /api/v1/cards/{card_id}/summary` uses the same persisted charge-summary source for its `charges`, `annual_fee`, `joining_fee`, `other_charges`, and `net_value` fields.
- Card-summary charge fields are month-scoped by the requested summary period. `category_id` still filters spend, but it does not re-slice persisted charge summaries in MVP.
- This card-level source of truth does not derive charges live from transactions at read time.

Dashboard and card analytics assumptions for the current MVP slice:

- Financial summaries exclude transactions where `duplicate_flag=true`.
- Analytics charges are derived live from persisted `transactions` rows where `is_card_charge=true`.
- `eligible_spend` is the sum of non-duplicate debit `txn_type=spend` transactions, so it currently matches `total_spend`.
- `reward_value` uses `reward_ledgers.reward_value_estimate` when present; otherwise it falls back to `reward_points * card.reward_conversion_rate`.
- Reward events are signed for analytics: `earned`, `cashback`, and positive `adjusted` rows add value; `redeemed` and `expired` rows reduce value.
- `net_value` is computed as `reward_value - charges`.

If you are using the Dockerized PostgreSQL service, start it first so the default `.env` database settings resolve:

```bash
docker compose -f infra/docker-compose.yml up -d postgres
```

## Run the frontend MVP shell

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The frontend runs on `http://127.0.0.1:3000` by default.

Frontend integration notes:

- Browser requests go through Next.js route handlers under `frontend/app/api/` so the JWT stays in an `httpOnly` session cookie.
- Protected backend requests proxy through `frontend/app/api/v1/[...path]/route.ts` and forward the bearer token from that cookie.
- Login, signup, logout, and session refresh use the real backend auth endpoints.
- The settings page uses a clearly isolated temporary adapter in `frontend/lib/mocks/settings.ts` because backend settings endpoints do not exist yet.

## Run with Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

The PostgreSQL container is published on `localhost:5433` by default.
The worker container runs automatically alongside the API container.

Once the services are up, run migrations in the API container:

```bash
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

## Test

```bash
cd backend
pytest
```

```bash
cd frontend
npm test
npm run build
```

## Migrations

Create a new migration after adding or changing ORM models:

```bash
cd backend
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```
