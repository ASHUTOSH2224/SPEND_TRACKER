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
- local-fake upload presign support for statement metadata
- authenticated statement metadata create/list/detail/retry/delete endpoints
- transaction explorer list/detail/update/bulk-update APIs
- transaction category audit logging for manual recategorization
- Docker compose support for backend plus PostgreSQL
- pytest smoke coverage

Statement ingestion, categorization, rewards, and analytics endpoints are still deferred.
This milestone only covers statement upload metadata and lifecycle state; it does not parse files yet.

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
- Docker and Docker Compose, if using the container workflow

## Local environment

1. Create a local environment file from the template.
2. Set either `DATABASE_URL` directly or the individual `POSTGRES_*` variables.
3. Set `AUTH_SECRET_KEY` for JWT signing. The checked-in default is for local development only.
4. Set `STORAGE_BACKEND=local_fake` unless you are wiring a different storage adapter.
5. The default template uses `localhost:5433` so the Dockerized PostgreSQL service does not collide with an existing local PostgreSQL server on `5432`.
6. Docker Compose overrides the backend container to use the internal database host `postgres:5432`.

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

Transaction endpoints:

- `GET /api/v1/transactions`
- `GET /api/v1/transactions/{transaction_id}`
- `PATCH /api/v1/transactions/{transaction_id}`
- `POST /api/v1/transactions/bulk-update`

Statement delete policy for the current MVP slice:

- `DELETE /api/v1/statements/{statement_id}` is blocked if the statement already has linked transactions.
- If a statement has no linked transactions, the route removes only the statement metadata row.
- The local fake storage backend does not delete any file blob.

If you are using the Dockerized PostgreSQL service, start it first so the default `.env` database settings resolve:

```bash
docker compose -f infra/docker-compose.yml up -d postgres
```

## Run with Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

The PostgreSQL container is published on `localhost:5433` by default.

Once the services are up, run migrations in the API container:

```bash
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

## Test

```bash
cd backend
pytest
```

## Migrations

Create a new migration after adding or changing ORM models:

```bash
cd backend
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```
