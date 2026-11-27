# Retail Refund Governance (ReturnGuard)

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-336791.svg)](https://www.postgresql.org/)
[![Keycloak 26](https://img.shields.io/badge/Keycloak-26-orange.svg)](https://www.keycloak.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)]()

> **Production-grade AI-assisted retail return request governance, policy verification, fraud risk scoring, and customer explanation platform.**

Retail Refund Governance is an end-to-end multi-tier platform designed to automate and adjudicate retail return claims safely. It combines a **FastAPI** backend, **PostgreSQL 18**, **MinIO S3** object storage, **Keycloak 26** PKCE authentication, an **ARQ/Redis** background worker, a multi-agent **LangGraph** review workflow, **Qdrant** hybrid policy RAG, **CatBoost** & **CLIP** forensic ML pipelines, optional **Langfuse** observability, and a modern **Next.js 16** frontend console.

---

## 📑 Table of Contents

- [Core Principles & Business Invariants](#-core-principles--business-invariants)
- [System Architecture](#-system-architecture)
  - [High-Level Topology](#high-level-topology)
  - [Dual Database Access Layer](#dual-database-access-layer)
- [Multi-Agent Review Pipeline](#-multi-agent-review-pipeline)
  - [Workflow Sequence](#workflow-sequence)
  - [Pipeline Visual Diagrams](#pipeline-visual-diagrams)
  - [Agent Roles & Short-Circuit Safeguards](#agent-roles--short-circuit-safeguards)
- [Web Interface & Review Console](#-web-interface--review-console)
- [Repository Layout](#-repository-layout)
- [Technology Stack](#-technology-stack)
- [Prerequisites & Dependencies](#-prerequisites--dependencies)
- [Step-by-Step Local Setup](#-step-by-step-local-setup)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [Identity & Seed Accounts](#-identity--seed-accounts)
- [REST API Reference](#-rest-api-reference)
- [Worker & LLM Execution Modes](#-worker--llm-execution-modes)
- [Policy Knowledge Base & RAG Indexing](#-policy-knowledge-base--rag-indexing)
- [Machine Learning & Forensic Services](#-machine-learning--forensic-services)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Infrastructure Operations](#-infrastructure-operations)

---

## 🛡️ Core Principles & Business Invariants

1. **Advisory AI Only (Zero Direct Fund Disbursement)**:
   The automated multi-agent pipeline generates typed decision proposals (`approved`, `denied`, or `escalated`) and customer-safe explanations. It **never** triggers payment gateway payouts or mutates money state directly.
2. **Deterministic Safeguards & Kill Switch**:
   Every AI recommendation is vetted by deterministic boundary guards (confidence $\ge 0.80$, behavior risk $\le 0.15$, max item value $\$250$). If the fail-safe `human_review_kill_switch` is active, all decisions are routed into the `review_queue` table for human oversight.
3. **Append-Only Audit Guarantees**:
   PostgreSQL database triggers (`audit_log_append_only`) forbid `UPDATE` and `DELETE` queries on the audit log.
4. **Strict Dual DB Isolation**:
   The web API utilizes SQLAlchemy 2.0 ORM over `asyncpg` for transactional integrity, while background workers run raw parameterized SQL via async `psycopg 3` connection pools with dictionary rows for ultra-low latency feature aggregation.
5. **Multi-Modal Evidence Verification**:
   Photographic evidence is verified using CLIP visual similarity against catalog photos, local AI-image detectors, and EXIF metadata heuristics before involving expensive vision LLMs.

---

## 🏛️ System Architecture

### High-Level Topology

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

### Dual Database Access Layer

To prevent ORM session locks and connection starvation between REST endpoints and background computation:
- **FastAPI Backend**: `postgresql+asyncpg://` via SQLAlchemy 2.0 async ORM (`backend/dependency.py`, `backend/app/models.py`).
- **Worker Pipeline**: `postgresql://` via `psycopg_pool.AsyncConnectionPool` executing raw parameterized SQL (`worker/pipeline/db.py`, `worker/pipeline/query.py`).

---

## 🤖 Multi-Agent Review Pipeline

The return review workflow is orchestrated as a state machine in **LangGraph** (`worker/pipeline/workflow.py`).

### Workflow Sequence

```text
[START]
   |
   v
[Data-Quality Gate] --- fails ---> Status = "in_review", halt to [END]
   | (ok)
   v
[Planner Agent] (selects evidence steps: image check, behavior analysis)
   |
   +---> [Intake Agent] --- mismatch / missing_info ---> Status = "denied", halt to [END]
   |        | (match)
   +---> [Policy Agent] --- ineligible / unclear ---> ineligible="denied", unclear="in_review", halt to [END]
   |        | (eligible=true)
   +---> [Image Agent] (CLIP similarity + AI detector + EXIF; if photo uploaded)
   |
   +---> [Behavior Agent] (CatBoost 10-feature classifier + risk summary)
   |
   v
[Decision Agent] (Deterministic validation safeguards; sets approved, denied, or escalated)
   |
   v
[Explanation Agent] (Generates plain-English, customer-safe rationale paragraph)
   |
   v
 [END]
```

### Pipeline Visual Diagrams

<table>
  <thead>
    <tr align="center">
      <th width="50%"><b>Part 1: Gate, Planner, Intake, and Policy Agents</b></th>
      <th width="50%"><b>Part 2: Image, Behavior, Decision, Critic, and Explanation Agents</b></th>
    </tr>
  </thead>
  <tbody>
    <tr align="center">
      <td><img src="assets/part1.png" alt="Full agent pipeline, part 1: data-quality gate, planner, intake, and policy" width="100%" /></td>
      <td><img src="assets/part2.png" alt="Full agent pipeline, part 2: image, behavior, decision, critic, and explanation" width="100%" /></td>
    </tr>
  </tbody>
</table>

### Agent Roles & Short-Circuit Safeguards

| Agent Node | Execution Mechanism | Responsibility & Guardrails | Short-Circuit Rules |
|---|---|---|---|
| **Data-Quality Gate** | Rule-based code | Verifies item name, product information, and mandatory photo requirements for damaged/defective items. | Fails: Case sets to `in_review`; halts workflow. |
| **Planner Agent** | Rule-based code | Schedules intake, policy retrieval, image checks (if photos present), and behavior scoring. | None. |
| **Intake Agent** | Structured Chat LLM | Validates customer return reason against purchased items, quantities, and order metadata. | `mismatch` or `missing_info`: Status sets to `denied`; halts. |
| **Policy Agent** | Hybrid Qdrant RAG + LLM | Retrieves policy clauses using Dense + Sparse BM25 RRF and verifies compliance (time window, condition). | `eligible=false`: `denied`; `unclear`: `in_review`; halts. |
| **Image Agent** | PyTorch / Transformers | Compares photo against catalog via CLIP (`openai/clip-vit-base-patch32`), detects AI images (`haywoodsloan/ai-image-detector-deploy`), checks EXIF tags, and invokes vision LLM fallback for borderline scores (0.60–0.75). | Failure recorded as evidence; continues workflow. |
| **Behavior Agent** | CatBoost Classifier + LLM | Computes risk probability from 10 tabular customer features and formats risk explanation. | Failure recorded as evidence; continues workflow. |
| **Decision Agent** | Structured Chat LLM + Guard | Synthesizes all evidence into a proposal. Overrides unsafe approvals; enforces $\le \$250$ cap, $\ge 0.80$ confidence, and $\le 0.15$ behavior risk. | Proposes `approved`, `denied`, or `escalated`. |
| **Explanation Agent**| Structured Chat LLM | Drafts one customer-facing paragraph explaining the outcome without exposing internal risk thresholds or fraud indicators. | Uses deterministic safe fallback if LLM times out or fails. |

---

## 🖥️ Web Interface & Review Console

The frontend is a **Next.js 16** web application featuring customer self-service portals and reviewer consoles.

### Return Review Dashboard
Inspect all submitted return requests with instant filtering by status, search by order or reason code, and real-time KPI overview metrics. Reviewers can drill into customer order details and uploaded evidence photos.

<p align="center">
  <img src="assets/return_review.png" alt="Return Review Interface" width="1200" />
</p>

### AI Proposed Decision Console
When cases require human escalation or oversight, reviewers can inspect the AI's proposal alongside confidence metrics, behavioral risk ratings, triggered policy clauses, and step-by-step pipeline execution traces.

<p align="center">
  <img src="assets/ai_proposed.png" alt="AI Proposed Decision" width="1200" />
</p>

### Auto-Approved Return Mode
Low-risk returns that meet all policy conditions, pass photo forensics, and maintain clean behavioral records receive an automated approval recommendation with full audit logging.

<p align="center">
  <img src="assets/Auto-approve.png" alt="Auto-Approved Return" width="1200" />
</p>

---

## 📁 Repository Layout

```text
Retail-Refund/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── models.py         # SQLAlchemy 2.0 ORM models
│   │   ├── schemas.py        # Pydantic v2 schemas
│   │   ├── config.py         # Application settings
│   │   ├── router/           # Endpoints: auth, shop, order, returns
│   │   ├── security/         # Keycloak RS256 JWKS token validation
│   │   └── services/         # Storage (MinIO), Mail (MailHog), Queue (ARQ)
│   ├── alembic/              # Database migration scripts
│   └── main.py               # FastAPI entry point & lifespan
├── frontend/                 # Next.js 16 App Router UI
│   ├── app/                  # Routes (/dashboard, /orders, /order-review, /refunds, /products)
│   ├── components/           # Modular UI widgets, tables, modals, layouts
│   ├── context/              # AppContext & client state
│   ├── lib/                  # shop-api.ts, retail-api.ts, keycloak.ts
│   └── types/                # TypeScript shared interfaces
├── worker/pipeline/          # ARQ Background Worker & LangGraph
│   ├── workers.py            # ARQ WorkerSettings entry point
│   ├── jobs.py               # review_return background job
│   ├── workflow.py           # LangGraph state machine definition
│   ├── llm.py                # LLM router (live, mock, replay)
│   ├── nodes/                # Agent nodes (gate, planner, intake, policy, etc.)
│   ├── prompts/              # System prompt templates
│   ├── query.py              # Raw parameterized SQL queries
│   └── db.py                 # Async psycopg 3 connection pool
├── ml/                       # Machine Learning Services
│   ├── model_service.py      # CatBoost 10-feature behavioral classifier
│   ├── image_service.py      # CLIP similarity, AI detector & EXIF forensics
│   └── behaviour_risk_model.cbm # Pre-trained CatBoost model weights
├── knowledge/                # Policy RAG Knowledge Base
│   ├── knowledge_base.py     # PolicyKnowledgeBase (dense + sparse BM25 RRF)
│   ├── chunker.py            # Markdown section and clause parser
│   ├── embeddings.py         # FastEmbed dense embeddings service
│   ├── retriver.py           # CLI retrieval search utility
│   └── policies/             # Return policy Markdown documents
├── infra/                    # Infrastructure & Provisioning
│   ├── postgres/init.sql     # Database initialization script
│   └── keycloak/             # Keycloak realm export JSON
├── docs/                     # Architectural & Module Documentation
├── assets/                   # Architecture diagrams and UI screenshots
├── seed/                     # Development seed catalog & assets
├── docker-compose.yml        # Multi-service infrastructure definition
└── Makefile                  # Developer workflow automation targets
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend API** | Python 3.12, FastAPI, SQLAlchemy 2.0 (`asyncpg`), Alembic, Pydantic v2, PyJWT, Boto3 |
| **Worker & Agents**| ARQ, Redis 7, LangGraph, LangChain, `psycopg 3` (async pool), Langfuse |
| **Machine Learning**| CatBoost, PyTorch, HuggingFace Transformers (`clip-vit-base-patch32`, `ai-image-detector-deploy`), Pillow |
| **Knowledge & RAG**| Qdrant 1.19, FastEmbed (`BAAI/bge-small-en-v1.5`, `Qdrant/bm25`), Reciprocal Rank Fusion |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, `keycloak-js`, Lucide React |
| **Infrastructure** | Docker, Docker Compose, PostgreSQL 18, MinIO S3, Keycloak 26, MailHog |

---

## 📋 Prerequisites & Dependencies

Before running the application locally, ensure you have:
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (fast Python package manager)
- **Node.js 20+** and **npm**
- **Docker Engine** & **Docker Compose**
- *(Optional)* API key for **Groq** or **OpenAI** (only required if running worker in `LLM_MODE=live`)

---

## 🚀 Step-by-Step Local Setup

### 1. Clone & Configure Environment

Clone the repository and prepare your environment files:

```bash
git clone https://github.com/anishpandey7659/ai-retail-refund-governance.git
cd ai-retail-refund-governance

# Create root environment file from example
cp .env.example .env   # Or create .env as detailed in the Configuration section

# Create frontend environment file
cp frontend/.env.example frontend/.env.local
```

### 2. Install Dependencies

Using `uv` to synchronize backend, worker, ML, and developer dependencies:

```bash
# Python dependencies
uv sync --group backend --group worker --group dev

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Launch Infrastructure Services

Start the containerized services (PostgreSQL, MinIO, Qdrant, Keycloak, Redis, MailHog):

```bash
make up
# Or: docker compose up -d

# Verify all services are healthy:
make check
```

### 4. Apply Database Migrations & Ingest Policy RAG

Run Alembic migrations to set up database schemas and index return policies into Qdrant:

```bash
# Run PostgreSQL migrations
uv run alembic -c backend/alembic.ini upgrade head

# Ingest policy markdown into Qdrant vector database
uv run python -m knowledge.knowledge_base
```

### 5. Seed Demo Catalog (Optional)

Populate product catalog and seed images into PostgreSQL and MinIO:

```bash
make seed
```

### 6. Run the Application

Start the API, Worker, and Frontend in separate terminals:

```bash
# Terminal 1: FastAPI Backend (Port 8000)
make run
# Or: uv run uvicorn backend.main:app --reload --port 8000

# Terminal 2: ARQ Review Worker
make worker
# Or: uv run arq worker.pipeline.workers.WorkerSettings

# Terminal 3: Next.js Frontend (Port 3000)
cd frontend && npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to open the web portal!

---

## ⚙️ Configuration & Environment Variables

All core parameters are configured in the root `.env` file:

| Variable | Required | Default / Local Target | Description |
|---|---|---|---|
| `POSTGRES_USER` | Yes | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | `postgres` | PostgreSQL password |
| `POSTGRES_DB` | Yes | `returnguard` | PostgreSQL database name |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/returnguard` | AsyncPG connection string (Backend & Alembic) |
| `DATABASE_PSYCOPG_URL`| Yes | `postgresql://postgres:postgres@localhost:5432/returnguard` | Psycopg connection string (ARQ Worker) |
| `MINIO_ROOT_USER` | Yes | `minioadmin` | MinIO root admin user |
| `MINIO_ROOT_PASSWORD` | Yes | `minioadmin` | MinIO root admin password |
| `MINIO_ENDPOINT` | Yes | `localhost:9000` | MinIO S3 endpoint |
| `MINIO_ACCESS_KEY` | Yes | `minioadmin` | S3 client access key |
| `MINIO_SECRET_KEY` | Yes | `minioadmin` | S3 client secret key |
| `MINIO_BUCKET_NAME` | Yes | `returnguard` | S3 bucket for product/return images |
| `MINIO_SECURE` | No | `false` | Whether to use SSL for MinIO |
| `KEYCLOAK_URL` | Yes | `http://localhost:8081` | Keycloak base URL for JWKS discovery |
| `KEYCLOAK_REALM` | Yes | `returnguard` | Keycloak application realm |
| `KEYCLOAK_CLIENT_ID` | Yes | `retail-api` | Expected access-token audience |
| `REDIS_URL` | Yes | `redis://localhost:6380/0` | Redis broker URL for ARQ jobs |
| `QDRANT_URL` | No | `http://localhost:6333` | Qdrant vector database URL |
| `QDRANT_COLLECTION` | No | `returnguard_policies` | Collection name for policy embeddings |
| `LLM_MODE` | No | `live` | Worker LLM mode (`live`, `mock`, `replay`) |
| `LLM_PROVIDER` | No | `groq` | Primary LLM provider (`groq`, `openai`) |
| `GROQ_API_KEY` | As needed| `None` | API key for Groq |
| `OPENAI_API_KEY` | As needed| `None` | API key for OpenAI |
| `LANGFUSE_PUBLIC_KEY`| No | `None` | Langfuse tracing public key |
| `LANGFUSE_SECRET_KEY`| No | `None` | Langfuse tracing secret key |

---

## 🔑 Identity & Seed Accounts

Authentication uses Keycloak OpenID Connect with PKCE on the frontend and stateless RS256 JWKS validation on the backend.

### Pre-configured Development Accounts

| Role | Username / Email | Password | Permissions & Access |
|---|---|---|---|
| **Customer** | `customer1@gmail.com` | `customer123` | Browse catalog, create orders, view personal orders, submit returns. |
| **Reviewer** | `reviewer1@returnguard.local` | `reviewer1` | Review pending orders, mark delivered, review return claims & AI proposals. |
| **Reviewer** | `reviewer2@returnguard.local` | `reviewer2` | Additional reviewer account for concurrency testing. |
| **Admin** | `admin1@returnguard.local` | `admin1` | Full administrative control: product creation, all orders, all return adjudications. |

---

## 📡 REST API Reference

Interactive OpenAPI documentation is hosted at `http://localhost:8000/docs`.

### Key Endpoints

- **System Health**:
  - `GET /health` — Verifies database connection pool.
- **Products & Catalog** (`backend/app/router/shop.py`):
  - `GET /products` — List catalog products with pagination, category filter, and presigned image URLs.
  - `GET /products/{product_id}` — Get single product details.
  - `POST /products` — Upload multipart product details with photo (Admin/Reviewer).
- **Orders** (`backend/app/router/order.py`):
  - `POST /orders` — Checkout order with idempotent key and stock validation.
  - `GET /orders` — List authenticated customer's orders.
  - `GET /orders/review` — Reviewer pending order queue.
  - `POST /orders/{order_id}/delivered` — Mark order item delivered.
- **Returns & Claims** (`backend/app/router/returns.py`):
  - `POST /returns` — Submit return claim with evidence photo (enqueues `review_return`).
  - `GET /returns` — List authenticated customer's return claims.
  - `GET /returns/review` — Reviewer queue of all customer returns.
  - `GET /returns/review/{return_id}` — Detailed return claim with presigned evidence photos.
- **Identity** (`backend/app/router/auth.py`):
  - `GET /auth/me` — Syncs Keycloak user profile and returns user role.

---

## 🔄 Worker & LLM Execution Modes

The review worker supports three execution modes (`worker/pipeline/llm.py`), enabling continuous integration testing without external API costs or credentials:

1. **`LLM_MODE=live`** *(Default)*:
   Dispatches requests to the primary LLM provider (Groq or OpenAI) with automatic fallback chains and Pydantic structured output validation.
2. **`LLM_MODE=mock`**:
   Generates deterministic responses based on `LLM_SCENARIO`:
   - `low_risk` — Clean customer history, valid product photo, policy approved.
   - `high_risk` — Excessive dispute rate, wardrobing pattern, escalated.
   - `suspicious` — AI-generated photo or mismatched CLIP score.
   - `defective_product` — Defective return reason matching policy rules.
   - Fault scenarios: `llm_failure`, `malformed_response`, `decision_failure`.
3. **`LLM_MODE=replay`**:
   Reads exact recorded mock agent responses from `LLM_REPLAY_FILE` for deterministic regression testing.

---

## 📚 Policy Knowledge Base & RAG Indexing

Policy documents located in `knowledge/policies/` are parsed and indexed into Qdrant for hybrid dense and sparse search:
- **Chunker**: Section-aware hierarchical markdown parser preserving document structure, titles, and clause IDs (`knowledge/chunker.py`).
- **Dense Vector**: `BAAI/bge-small-en-v1.5` (or OpenAI `text-embedding-3-small`) via FastEmbed (`knowledge/embeddings.py`).
- **Sparse Vector**: `Qdrant/bm25` for exact token and clause number matching (`knowledge/knowledge_base.py`).
- **Fusion**: Merges dense and sparse candidates via **Reciprocal Rank Fusion (RRF)**.

Inspect vectors and payloads via the Qdrant Dashboard at [http://localhost:6333/dashboard](http://localhost:6333/dashboard).

---

## 🔬 Machine Learning & Forensic Services

The `ml/` package provides local inference engines:

### 1. Behavior Risk Classification (`ml/model_service.py`)
- **Model**: CatBoost multi-class classifier (`ml/behaviour_risk_model.cbm`).
- **Target Classes**: `legitimate` (0), `policy_abuser` (1), `fraudulent_return` (2), `wardrobing` (3).
- **Features Evaluated**: Return rate percentage, customer support contacts, refund-to-order ratio, dispute count, packaging opened, multiple linked accounts, cross-account refund destination, requested amount, return reason, address changes before delivery.

### 2. Multi-Modal Image Forensics (`ml/image_service.py`)
- **CLIP Similarity**: Compares return photo against catalog photo (`openai/clip-vit-base-patch32`). Thresholds: $\ge 0.75$ (Match), $0.60 - 0.75$ (Borderline), $< 0.60$ (Mismatch).
- **AI-Generated Image Detector**: Scores image against `haywoodsloan/ai-image-detector-deploy` (flags if $p > 0.50$).
- **EXIF Forensics**: Detects generative software tags (`midjourney`, `stable diffusion`, `dall-e`), standard AI canvas dimensions (e.g., $1024 \times 1024$), and camera metadata anomalies.
- **Vision LLM Fallback**: Invokes `gpt-4o` (with `gpt-4o-mini` fallback) strictly for borderline CLIP scores.

---

## 🧪 Testing & Quality Assurance

Run the test suite across backend, worker, and machine learning components:

```bash
# Run all Python unit and integration tests
uv run --group backend --group worker --group dev pytest

# Run authentication and security tests
uv run --group backend --group dev pytest test/test_auth.py

# Run mock & replay workflow tests
uv run --group worker --group dev pytest test/test_workflow.py

# Code linting and formatting
uv run --group dev ruff check .

# Frontend linting and typechecking
cd frontend && npm run lint && npm run build
```

---

## 🚢 Infrastructure Operations

| Port | Service | Description | Console URL |
|---|---|---|---|
| `3000` | Frontend UI | Next.js Web App | [http://localhost:3000](http://localhost:3000) |
| `8000` | FastAPI | REST API & Docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| `8081` | Keycloak | Identity Management | [http://localhost:8081/admin](http://localhost:8081/admin) (admin / admin) |
| `9000` / `9001` | MinIO | S3 Object Storage | [http://localhost:9001](http://localhost:9001) (minioadmin / minioadmin) |
| `6333` | Qdrant | Vector Database | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) |
| `6380` | Redis | Job Queue Broker | `redis://localhost:6380/0` |
| `8025` | MailHog | Transactional Email UI | [http://localhost:8025](http://localhost:8025) |
| `5432` | PostgreSQL | Relational Database | `localhost:5432/returnguard` |

### Makefile Automation Shortcuts

```bash
make up       # Start all Docker Compose services in background
make check    # Verify container status and healthchecks
make seed     # Populate database and MinIO with demo catalog items
make run      # Start FastAPI backend server with hot-reload
make worker   # Launch the ARQ LangGraph background review worker
make stop     # Stop containers preserving container state and volumes
make down     # Tear down containers and networks (preserves named volumes)
```

---

## 📄 License & Compliance

This project is a reference implementation and demonstration of AI governance patterns in retail e-commerce. Always ensure compliance with customer privacy regulations, data retention policies, and fair credit reporting guidelines before deploying to production environments.
