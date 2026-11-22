# System Architecture

> Last verified against commit: `c39ba3f`

## Overview
Retail Refund Governance is a multi-tier platform that processes retail returns through automated multi-agent risk assessment, policy verification, and human reviewer oversight.

```text
                     +---------------------------------------+
                     |         Browser / Next.js UI          |
                     |  (Keycloak PKCE Auth, Port 3000)      |
                     +-------------------+-------------------+
                                         |
                       REST API Calls    |   Token Validation
                                         v   (JWKS RS256)
+----------------------------------------+-------------------+
|                           FastAPI Backend (Port 8000)      |
+----+-------------------+-------------------+---------------+
     |                   |                   |
     | asyncpg           | boto3             | ARQ enqueue
     v                   v                   v
+----+---------+   +-----+---------+   +-----+---------+
| PostgreSQL   |   |   MinIO S3    |   | Redis (6380)  |
| (Port 5432)  |   | (Port 9000)   |   +-------+-------+
+--------------+   +---------------+           |
                                               | Worker job pull
                                               v
                   +---------------------------+-------------+
                   |       ARQ Review Worker                 |
                   |   (worker.pipeline.workers)             |
                   +----+-------------------+----------------+
                        |                   |
                        | Direct psycopg    | Hybrid Search
                        v                   v
                   +----+---------+   +-----+---------+
                   |  PostgreSQL  |   | Qdrant Vector |
                   |  (raw SQL)   |   | (Port 6333)   |
                   +--------------+   +---------------+
                        |
                        +---> ml/ (CatBoost Risk Model & CLIP Image Analysis)
                        +---> worker/pipeline/workflow.py (LangGraph Flow)
```

## Cross-Module Contracts

### 1. Backend to Worker (ARQ Enqueue) [Implemented]
- **Mechanism**: Backend calls `enqueue_review(return_id)` (`backend/app/services/queue.py`), creating an ARQ pool connected to `REDIS_URL` (`redis://localhost:6380/0`).
- **Function Registered**: `review_return(ctx: dict, return_id: str)` in `worker/pipeline/jobs.py` registered on `WorkerSettings.functions` (`worker/pipeline/workers.py`).
- **Queue Name**: `arq:queue`.
- **Payload Shape**: A single argument `return_id` (string UUID).

### 2. Database Access Separation [Implemented]
- **FastAPI Backend**: Uses SQLAlchemy 2.0 with `postgresql+asyncpg://` (`backend/dependency.py`, `backend/app/models.py`). Handles ORM mappings, relations, and table creation.
- **Worker Pipeline**: Does **not** use SQLAlchemy models. Uses `psycopg_pool.AsyncConnectionPool` (`worker/pipeline/db.py`) executing raw SQL queries (`RETURN_QUERY`, `ML_CONTEXT_QUERY` in `worker/pipeline/query.py`) returning dictionaries via `dict_row`.
- **Human Review Queue**: Worker writes pending human review cases directly to `review_queue` table with JSONB case dumps (`worker/pipeline/helper.py`).

### 3. Pipeline to ML & Knowledge Contracts [Implemented]
- **Behavior Risk**: `worker/pipeline/nodes/agents.py` calls `risk_probability(model, X)` from `ml/model_service.py`, evaluating 10 tabular features extracted by `ML_CONTEXT_QUERY`.
- **Image Forensics**: `worker/pipeline/nodes/agents.py` calls `analyze_image(...)` in `ml/image_service.py`, which fetches photos from MinIO via `backend.app.services.storage.download_image`.
- **Policy Knowledge Base**: `worker/pipeline/dependency.py` instantiates `PolicyKnowledgeBase()` from `knowledge/knowledge_base.py`, querying collection `returnguard_policies` via Qdrant hybrid search.

### 4. Identity & Authentication [Implemented]
- **Provider**: Keycloak 26 on port 8081 (realm `returnguard`).
- **Frontend**: Authenticates using `keycloak-js` with OAuth2 Authorization Code Flow + PKCE (`frontend/lib/keycloak.ts`).
- **Backend**: `backend/app/security/auth.py` decodes JWTs using RS256 with keys fetched from Keycloak JWKS endpoint (`/protocol/openid-connect/certs`). Extracts roles (`admin`, `reviewer`, default `customer`) and syncs user to `users` table.

### 5. Storage & Notifications [Implemented]
- **MinIO**: Product images and customer return photos stored in bucket `returnguard`. Public presigned URLs are generated for client display.
- **MailHog**: Transactional emails (order confirmation, return submission receipts) sent via local SMTP `mailhog:1025` (`backend/app/services/mail.py`).

## Service Ports & Infrastructure

| Service | Container Image | Host Port | Purpose |
|---|---|---|---|
| PostgreSQL | `postgres:18` | `5432` | Application & Keycloak relational datastore |
| MinIO | `cgr.dev/chainguard/minio:latest` | `9000` (API), `9001` (Console) | S3-compatible image storage |
| Qdrant | `qdrant/qdrant:v1.19.0` | `6333` (REST), `6334` (gRPC) | Vector database for hybrid policy RAG |
| Keycloak | `quay.io/keycloak/keycloak:26.7.2` | `8081` (Host) -> `8080` (Internal) | IAM OpenID Connect provider |
| Redis | `redis:7-alpine` | `6380` (Host) -> `6379` (Internal) | ARQ background job queue |
| MailHog | `mailhog/mailhog:v1.0.1` | `1025` (SMTP), `8025` (Web UI) | Local email inspection service |
| Backend API | Local Python (Uvicorn) | `8000` | FastAPI HTTP REST API |
| Frontend | Local Next.js | `3000` | Web application user interface |
