# Retail Refund Governance

> AI-assisted retail return request review, policy verification, fraud risk scoring, and customer explanation generation.

## Stack
- **Backend:** FastAPI, SQLAlchemy 2.0 (asyncpg), Alembic, Pydantic v2, PyJWT.
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, `keycloak-js`.
- **Worker & Agents:** ARQ, Redis 7, LangGraph, CatBoost, HuggingFace Transformers (CLIP, AI detector), Langfuse.
- **Datastores & Infra:** PostgreSQL 18, MinIO S3, Qdrant (hybrid vector), Keycloak 26, MailHog.

## High-Level Architecture
1. **Frontend** initiates Keycloak PKCE auth and calls FastAPI endpoints (`/products`, `/orders`, `/returns`).
2. **FastAPI** records returns, uploads evidence photos to MinIO, and enqueues `review_return` to Redis.
3. **ARQ Worker** loads return context via raw SQL (`psycopg 3`) and executes the **LangGraph** pipeline.
4. **LangGraph Pipeline** runs Gate → Planner → Intake → Policy (Qdrant RAG) → Image (CLIP/detector) & Behavior (CatBoost) → Decision safeguards → Customer explanation.
5. **Human Review**: If kill-switch is active or case is escalated, record is pushed to `review_queue`.

## Key Code Conventions
- **Status tags**: Tag documentation claims as `[Implemented]`, `[Planned]`, or `[Unverified]`.
- **Dual DB drivers**: Backend uses `postgresql+asyncpg://` via SQLAlchemy ORM; worker uses `postgresql://` via async `psycopg 3` connection pool with raw SQL dictionaries (`dict_row`).
- **Audit safety**: Append-only DB triggers protect `audit_log`; decision proposals update return status but never disburse refunds directly.
- **Fail-safe auth**: Keycloak RS256 token verification with JWKS public key caching in backend; PKCE in browser.

## Task-to-Files Routing Table

| Task Category | Primary Files to Read |
|---|---|
| New or changed API endpoint | `backend/AGENTS.md`, `docs/backend/API.md` |
| DB model or schema migration | `backend/AGENTS.md`, `docs/backend/DATABASE.md` |
| Auth, login, roles, permissions | `docs/backend/AUTH.md`, `infra/AGENTS.md` |
| UI page or frontend component | `frontend/AGENTS.md`, `docs/frontend/OVERVIEW.md` |
| Frontend-to-API data integration | `frontend/AGENTS.md`, `docs/frontend/DATA_FLOW.md`, `docs/backend/API.md` |
| Agent logic or review workflow | `worker/pipeline/AGENTS.md`, `docs/pipeline/WORKFLOW.md` |
| Policy retrieval or Qdrant RAG | `knowledge/AGENTS.md`, `docs/knowledge/RAG.md` |
| Image analysis or behavior ML model | `ml/AGENTS.md`, `docs/ml/SERVICES.md` |
| Docker Compose, env vars, infra | `infra/AGENTS.md`, `docs/infra/DOCKER.md`, `docs/infra/CONFIGURATION.md` |

## Session Startup Rules for Agents
1. **First step**: Read root `AGENTS.md`.
2. **Navigation**: Use `docs/CODEBASE_MAP.md` to locate architectural modules and entry points.
3. **Scope isolation**:
   - Frontend-only tasks: Read `frontend/AGENTS.md` and `docs/frontend/*`; do NOT load backend source.
   - Backend-only tasks: Read `backend/AGENTS.md` and `docs/backend/*`; do NOT load frontend source.
   - Pipeline/ML tasks: Read `worker/pipeline/AGENTS.md`, `ml/AGENTS.md`, `docs/pipeline/*`, `docs/ml/*`.
   - Cross-boundary tasks: Load both nested `AGENTS.md` and the relevant contract docs.
4. **File inspection**: Inspect specific source files only when required; never recursively scan the repository.
5. **Precedents**: Match existing coding styles, models, and naming conventions.

## Do-Not-Read List
Unless specifically required by the task, do NOT inspect:
- `node_modules/`, `.next/`, build directories, or caches (`.ruff_cache/`, `.pytest_cache/`, `__pycache__/`).
- Lockfiles (`package-lock.json`, `uv.lock`).
- `backend/alembic/versions/` (refer to `docs/backend/DATABASE.md` instead).
- `seed/` data files and images (`seed/products.json`, `seed/images/`).
- Policy markdown sources in `knowledge/policies/` (refer to `docs/knowledge/RAG.md` instead).

## Documentation Maintenance Rules
- Update docs when architecture, API contracts, schemas, or module boundaries change.
- Update `docs/CODEBASE_MAP.md` whenever modules or entry points change.
- Document architectural design choices in `docs/DECISIONS.md`.
- Never commit docs that contradict the source code.

## Source of Truth

- Actual source code is the authority for current implementation.
- Documentation provides architectural context, not proof of implementation.
- Verify relevant source files before modifying existing behavior.
- If documentation conflicts with source code, trust the source code
  and update the affected documentation.
- Never invent functions, classes, endpoints, database columns,
  or configuration variables based solely on documentation.

## Scope Isolation

- Load only the documentation and source files relevant to the task.
- Do not explore unrelated modules.
- For frontend-only UI changes, avoid backend exploration.
- For API integration, inspect the relevant backend API contract.
- For cross-module changes, inspect both sides of the integration.
- Expand scope only when implementation dependencies require it.

## Implementation Workflow

1. Understand the requested change and identify its scope.
2. Read relevant module instructions and documentation.
3. Inspect existing implementation before coding.
4. Identify dependencies and potential side effects.
5. Implement using existing project conventions.
6. Run relevant tests, linting, and type checks.
7. Review the final diff for unintended changes.
8. Update affected documentation.

Never modify unrelated files or perform broad refactoring
unless explicitly required.

## Testing Requirements

- Run targeted tests before running the complete test suite.
- Add or update tests for new functionality.
- Test error handling and failure paths.
- Validate API contracts when modifying endpoints.
- Validate database migrations when modifying schemas.
- Do not claim tests passed unless they were actually executed.
- Report skipped tests and known failures explicitly.

## Security and Business Invariants

- Never expose secrets, tokens, or credentials in source code or logs.
- Never bypass Keycloak authentication or authorization.
- Validate user ownership before accessing customer resources.
- Never allow AI agents to directly disburse refunds.
- Preserve append-only audit log guarantees.
- Treat uploaded files and customer input as untrusted data.
- Do not weaken authorization or validation to make tests pass.

## Completion Report

After completing a task, report:

- Summary of implemented changes.
- Files created, modified, or deleted.
- Tests and validation performed.
- Test results.
- Documentation updated.
- Known issues or remaining work.

Never claim successful implementation without verification.