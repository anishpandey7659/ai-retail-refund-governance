# Backend Agent Guide

## Responsibilities & Stack
- **Scope**: FastAPI REST API, database models, migrations, authentication, object storage, and job queueing.
- **Stack**: FastAPI, SQLAlchemy 2.0 (asyncpg), Alembic, Pydantic v2, PyJWT, boto3.

## Key Directories & Entry Points
- `backend/main.py`: Application entry point and router assembly.
- `backend/dependency.py`: Database lifespan manager and async session dependency (`get_db_session`).
- `backend/app/router/`: Route handlers (`shop.py`, `order.py`, `returns.py`, `auth.py`).
- `backend/app/models.py`: SQLAlchemy database models.
- `backend/app/schemas.py`: Pydantic request and response schemas.
- `backend/app/security/auth.py`: Keycloak RS256 token verification and role guards.
- `backend/app/services/`: `storage.py` (MinIO & DB), `mail.py` (MailHog), `queue.py` (ARQ dispatch).

## Conventions & Rules
- Backend uses `postgresql+asyncpg://` via SQLAlchemy ORM; do not import worker psycopg helpers here.
- Protect endpoints with `require_role("customer" | "reviewer" | "admin")`.
- Enqueue return review jobs via `enqueue_review(return_id)`.
- Enforce append-only audit log rules; never bypass `audit_log_append_only`.

## Testing & Execution
- Run API: `uv run uvicorn backend.main:app --reload` (Port 8000).
- Run migrations: `uv run alembic -c backend/alembic.ini upgrade head`.
- Run tests: `uv run --group backend --group dev pytest test/test_auth.py`.

## Docs to Read
- `docs/backend/API.md`, `docs/backend/DATABASE.md`, `docs/backend/AUTH.md`.
