# Worker Pipeline Agent Guide

## Responsibilities & Stack
- **Scope**: Background return review jobs, LangGraph workflow execution, deterministic decision safeguards.
- **Stack**: ARQ, Redis, LangGraph, async `psycopg 3`, CatBoost, Transformers, Langfuse.

## Key Directories & Entry Points
- `worker/pipeline/workers.py`: ARQ `WorkerSettings` (entry point for `make worker`).
- `worker/pipeline/jobs.py`: Job definition `review_return(ctx, return_id)`.
- `worker/pipeline/workflow.py`: LangGraph state machine (`run_workflow`).
- `worker/pipeline/nodes/`: Agent implementations (`agents.py`, `agent_helpers.py`, `base.py`).
- `worker/pipeline/prompts/`: Prompt templates (`intake.py`, `policy.py`, `decision.py`, etc.).
- `worker/pipeline/query.py`: Direct raw SQL queries (`RETURN_QUERY`, `ML_CONTEXT_QUERY`).
- `worker/pipeline/db.py`: Async `psycopg` connection pool.

## Conventions & Rules
- Worker does **not** use SQLAlchemy models; execute raw SQL queries via `_rows` in `db.py`.
- Decision agent produces proposals (`approved`, `denied`, `escalated`); it **never** disburses refunds.
- Fail-safe: When `human_review_kill_switch` is ON, insert case into `review_queue` table.
- Agent failures must be recorded on `case.agent_results`; do not allow an agent crash to crash the workflow.

## Testing & Execution
- Run worker: `make worker` or `uv run arq worker.pipeline.workers.WorkerSettings`.
- Test worker job: `uv run python -m scripts.test_worker`.
- Run tests: `uv run --group worker --group dev pytest test/test_workflow.py`.

## Docs to Read
- `docs/pipeline/WORKFLOW.md`, `docs/ml/SERVICES.md`, `docs/knowledge/RAG.md`.
