# Codebase Map

> Last verified against commit: `c39ba3f`

| Module | Location | Responsibility | Key Entry Points | Depends On | Docs |
|---|---|---|---|---|---|
| **API Backend** | `backend/` | FastAPI REST API, authentication enforcement, database models, Alembic migrations, MinIO presigning, ARQ job enqueueing. | `backend/main.py`<br>`backend/dependency.py`<br>`backend/app/router/*.py` | PostgreSQL, Redis, MinIO, Keycloak, MailHog | `docs/backend/API.md`<br>`docs/backend/DATABASE.md`<br>`docs/backend/AUTH.md` |
| **Web Frontend** | `frontend/` | Next.js 16 web interface for customer catalog, orders, return requests, and reviewer queues. | `frontend/app/layout.tsx`<br>`frontend/app/page.tsx`<br>`frontend/context/app-context.tsx` | Backend API, Keycloak | `docs/frontend/OVERVIEW.md`<br>`docs/frontend/DATA_FLOW.md` |
| **Review Worker** | `worker/pipeline/` | Background ARQ worker executing the LangGraph return review graph, deterministic safeguards, mock/replay LLM testing, and human review queue. | `worker/pipeline/workers.py`<br>`worker/pipeline/jobs.py`<br>`worker/pipeline/workflow.py`<br>`worker/pipeline/llm.py`<br>`worker/pipeline/mock_llm.py` | PostgreSQL, Redis, `ml/`, `knowledge/`, Langfuse | `docs/pipeline/WORKFLOW.md` |
| **Machine Learning** | `ml/` | Tabular CatBoost customer risk classification and multi-modal image forensics (CLIP, AI detector, EXIF). | `ml/model_service.py`<br>`ml/image_service.py` | `ml/behaviour_risk_model.cbm`, HuggingFace models, MinIO | `docs/ml/SERVICES.md` |
| **Knowledge Base** | `knowledge/` | Policy document chunking, FastEmbed embeddings, and Qdrant hybrid (dense + BM25) retrieval. | `knowledge/knowledge_base.py`<br>`knowledge/retriver.py` | Qdrant, `knowledge/policies/` | `docs/knowledge/RAG.md` |
| **Infrastructure** | `infra/` | Container definitions, database bootstrap SQL, Keycloak realm export configuration. | `docker-compose.yml`<br>`infra/postgres/init.sql`<br>`infra/keycloak/realm-export.json` | Docker Engine, Docker Compose | `docs/infra/DOCKER.md`<br>`docs/infra/CONFIGURATION.md` |
| **Seed Utilities** | `seed/` | Catalog and image population script for local development. | `seed/seed.py`<br>`seed/products.json` | PostgreSQL, MinIO | `docs/CODEBASE_MAP.md` |
