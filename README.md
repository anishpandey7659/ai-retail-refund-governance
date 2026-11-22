# Retail Refund Governance

Retail Refund Governance is a demo application for submitting and reviewing
retail return requests. It combines a FastAPI backend, PostgreSQL, MinIO image
storage, Keycloak authentication, a Redis-backed ARQ worker, a LangGraph review
workflow, policy retrieval with Qdrant, and optional Langfuse tracing.

The review worker produces a recommendation and explanation. It does **not**
issue a refund or change the return's final status.

## What it does

- Lists products, creates orders, and accepts return requests.
- Stores product and return photos in MinIO.
- Authenticates users through Keycloak.
- Queues return reviews and risk predictions in Redis/ARQ.
- Checks return information, policy eligibility, optional product images, and
  customer behavior.
- Builds a typed decision proposal with deterministic safeguards.
- Retrieves policy passages from Qdrant using dense and sparse search.
- Optionally records workflow and agent input/output in Langfuse.

This is a demo project. Configure credentials and infrastructure for your own
environment before using it with real customer data.

## Architecture

```text
Client
  |
  v
FastAPI backend ---- PostgreSQL
  |                  MinIO (images)
  |                  Keycloak (identity)
  |
  +---- Redis queue ---- ARQ worker
                            |
                            v
                      LangGraph review
                       |    |     |
                       |    |     +-- Image/behavior checks as selected
                       |    +-------- Qdrant policy retrieval
                       +------------- LLM agents
                            |
                            +-- Optional Langfuse traces
```

### Full agent pipeline diagrams

The diagrams below show the complete return-review pipeline, from the
data-quality gate through the customer-facing explanation.

#### Part 1: Gate, planner, intake, and policy agents

![Full agent pipeline, part 1: data-quality gate, planner, intake, and policy](assets/part1.png)

#### Part 2: Image, behavior, decision, critic, and explanation agents

![Full agent pipeline, part 2: image, behavior, decision, critic, and explanation](assets/part2.png)

### Return-review workflow

```text
START
  |
  v
Data-quality gate -- fail --> END (return case without running agents)
  |
 pass
  v
Planner
  |
  v
Intake -- mismatch or missing_info --> END
  |
 match
  v
Policy -- eligible=false or unclear --> END
  |
 eligible=true
  v
Selected image/behavior checks (when applicable)
  |
  v
Decision proposal
  |
  v
Customer-safe explanation
  |
  v
 END
```

The planner selects image analysis when the case has photos and behavior
analysis when return history indicates prior returns or denials. Agent failures
are recorded; the workflow continues so the decision can safely account for
missing evidence. The policy and intake short-circuits above apply to returned
agent results, not agent exceptions.

## Repository layout

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI application, API routes, database models, and Alembic migrations |
| `worker/pipeline/` | ARQ jobs, LangGraph workflow, agents, prompts, and database queries |
| `ml/` | Image analysis and behavior model services |
| `knowledge/` | Policy chunking, embeddings, retrieval, and policy documents |
| `infra/` | PostgreSQL initialization, Keycloak realm export, and Qdrant notes |
| `seed/` | Product data and local seed utilities |
| `docker-compose.yml` | Local PostgreSQL, MinIO, Qdrant, Keycloak, Redis, and MailHog services |

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Docker Engine and Docker Compose
- API credentials for the configured LLM provider(s)

The image-analysis models and behavior-risk model may download model files on
their first run. Allow additional time and disk space for those initial
downloads.

## Local setup

1. Create a root-level `.env` file. Do not commit it. The Compose file and
   settings classes load configuration from this file.
2. Set the required Compose and application settings listed below. Use local
   ports for services accessed from your host and service names for connections
   made by containers.
3. Install the backend, worker, and development dependency groups:

   ```bash
   uv sync --group backend --group worker --group dev
   ```

4. Start the local infrastructure:

   ```bash
   docker compose up -d
   make check
   ```

5. Apply database migrations:

   ```bash
   uv run alembic -c backend/alembic.ini upgrade head
   ```

6. (Optional) Seed the product catalog:

   ```bash
   make seed
   ```

7. Start the API and worker in separate terminals:

   ```bash
   make run
   ```

   ```bash
   make worker
   ```

The API is available at `http://localhost:8000`. Interactive API documentation
is at `http://localhost:8000/docs`; the health endpoint is
`http://localhost:8000/health`.

### Environment settings

Set values appropriate for your local environment. These are names and
descriptions, not real credentials.
The frontend uses Keycloak Authorization Code flow with PKCE; configure the
public client in Keycloak with the frontend origin as a valid redirect/web
origin. Copy `frontend/.env.example` to `frontend/.env.local` and set its
values. Set the backend `KEYCLOAK_URL`, `KEYCLOAK_REALM`, and
`KEYCLOAK_CLIENT_ID` so the URL and audience match the access tokens issued by
your realm.

| Variable | Required | Purpose |
| --- | --- | --- |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Yes | PostgreSQL container credentials and database |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | Yes | MinIO container credentials |
| `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD` | Yes | Keycloak bootstrap administrator |
| `DATABASE_URL` | Yes | SQLAlchemy/asyncpg connection URL used by the API and migrations; use the `postgresql+asyncpg` driver scheme |
| `DATABASE_PSYCOPG_URL` | Yes for worker | Psycopg connection URL used by worker queries; use the `postgresql` driver scheme |
| `KEYCLOAK_URL` | Yes | Base Keycloak URL used to build the realm issuer and JWKS URL |
| `KEYCLOAK_REALM` | Yes | Realm containing the frontend and API clients |
| `KEYCLOAK_CLIENT_ID` | Yes | Expected access-token audience |
| `NEXT_PUBLIC_KEYCLOAK_URL` | Yes for frontend | Keycloak base URL used for browser login |
| `NEXT_PUBLIC_KEYCLOAK_REALM` | Yes for frontend | Realm used for browser login |
| `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` | Yes for frontend | Public Keycloak client configured for Authorization Code + PKCE |
| `REDIS_URL` | Yes for backend and worker | Redis connection URL; local Compose exposes `redis://localhost:6380/0` |
| `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET_NAME` | Yes for image operations | S3-compatible image storage; local bucket is `returnguard` |
| `MINIO_SECURE` | No | Whether the MinIO endpoint uses HTTPS; defaults to `false` |
| `GROQ_API_KEY`, `OPENAI_API_KEY` | As needed | Credentials for configured primary/fallback LLM providers |
| `LLM_PROVIDER`, `LLM_MODEL` | No | Primary LLM provider and model |

Run the authentication tests with:

```bash
uv run --group backend --group dev pytest test/test_auth.py
```
| `FALLBACK_LLM_PROVIDER`, `FALLBACK_LLM_MODEL` | No | Fallback provider and model |
| `IMAGE_MODEL` | No | Vision model setting |
| `QDRANT_URL`, `QDRANT_COLLECTION` | No | Policy vector database; defaults to `http://localhost:6333` and `returnguard_policies` |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | No | Enable Langfuse tracing when both are set |
| `LANGFUSE_BASE_URL` | No | Optional Langfuse server URL |

`docker-compose.yml` also expects the Keycloak realm export at
`infra/keycloak/realm-export.json`. Configure that realm, its clients, and the
issuer/JWKS URLs to match your local Keycloak instance.

## API overview

The API includes these route groups:

| Route | Description |
| --- | --- |
| `/health` | Database health check |
| `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me` | Keycloak-backed authentication |
| `/products` | Create and browse products |
| `/orders` | Checkout and list the authenticated user's orders |
| `/returns` | Submit and list return requests, and answer information requests |

Most order and return operations require a valid authenticated user. See
`/docs` for request schemas and the full route specification.

## Worker jobs

The ARQ worker registers:

- `review_return`: loads a return and runs the LangGraph review workflow.
- `predict_return_risk`: loads behavior features and returns the saved model's
  prediction.

Return submission queues `review_return` through Redis. Run the worker using
`make worker` so queued jobs can be processed.

## Policy retrieval

Policy content is split into chunks, embedded, and indexed in Qdrant. The
worker searches the `returnguard_policies` collection using dense embeddings
and sparse BM25 retrieval. Ensure the policy collection has been ingested
before expecting policy-agent retrieval to return results. The Qdrant dashboard
is available at `http://localhost:6333/dashboard`.

The active demo policy is in `knowledge/policies/Policy.md`.

## Tracing and data handling

When both Langfuse keys are configured, the workflow records a root trace and
agent observations. Agent observations include the case input and agent output
payloads, which can contain customer and return information. Use demo data or
configure appropriate access controls, retention, and redaction before enabling
tracing with real customer information. Keep all API keys and passwords out of
tracked files.

## Development and tests

Run the test suite with:

```bash
uv run --group backend --group worker --group dev pytest
```

Run Ruff on the Python project with:

```bash
uv run --group dev ruff check .
```

Useful infrastructure commands:

```bash
docker compose ps
make stop
make down
```

`make stop` stops containers but preserves them and their data volumes.
`make down` removes the containers and network; named data volumes are retained
unless explicitly removed.
