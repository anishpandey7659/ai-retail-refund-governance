# LangGraph Review Workflow & Worker Jobs

> Last verified against commit: `c39ba3f`

## ARQ Worker Execution (`worker/pipeline/`)
- **Entry point**: `worker/pipeline/workers.py:WorkerSettings`. Run via `make worker` or `uv run arq worker.pipeline.workers.WorkerSettings`.
- **Registered job**: `review_return(ctx: dict, return_id: str)` in `worker/pipeline/jobs.py`.
- **DB Connection**: Async `psycopg 3` pool initialized during ARQ startup (`worker/pipeline/db.py`). Uses raw SQL in `worker/pipeline/query.py`.
- **Customer email**: When automatic review is enabled, `review_return` sends the review message using `backend.app.services.mail.send` and the customer email loaded with the return context. Human-review cases do not receive an automated decision email.
- **Tracing**: Langfuse integration in `worker/pipeline/tracing.py`. Enabled if `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are provided.

## Workflow Sequence (`worker/pipeline/workflow.py`)

```text
[START]
   |
   v
[Data-Quality Gate] --- fails ---> Status = "in_review", halt to [END]
   | (ok)
   v
[Planner] (selects evidence steps)
   |
   +---> [Intake Agent] --- mismatch/missing ---> Status = "denied", halt to [END]
   |        | (match)
   +---> [Policy Agent] --- ineligible/unclear ---> ineligible="denied", unclear="in_review", halt to [END]
   |        | (eligible=true)
   +---> [Image Agent] (CLIP + detector; if photo exists)
   |
   +---> [Behavior Agent] (CatBoost risk model; if customer history warrants)
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

## Agent Details & Prompts

| Agent Node | Handler | Prompts & Rules | Short-Circuit Rules |
|---|---|---|---|
| **Data Gate** | `agents.py:data_quality_gate` | Pure rule-based code. Validates item name, required photos for reason code, and product info. | If invalid: stops workflow, sets `case.status = "in_review"`. |
| **Planner** | `agents.py:planner` | Deterministic logic: schedules intake and policy; adds image check if photos exist; adds behavior check if `returns >= 2` or `denied > 0`. | None. |
| **Intake** | `agents.py:intake` | `worker/pipeline/prompts/intake.py`. Evaluates submission vs purchased product. | If `mismatch` or `missing_info`: stops workflow, sets `case.status = "denied"`. |
| **Policy** | `agents.py:policy` | `worker/pipeline/prompts/policy.py`. Queries Qdrant hybrid index. | If `eligible=false`: `denied`; if `unclear`: `in_review`. Both halt. |
| **Image** | `agents.py:image` | `worker/pipeline/prompts/image.py`. Calls `ml/image_service.py` (CLIP, AI detector, EXIF, vision model). | Exceptions recorded on case; does not halt. |
| **Behavior** | `agents.py:behavior` | `worker/pipeline/prompts/behavior.py`. Evaluates CatBoost tabular model via `ml/model_service.py`. | Exceptions recorded on case; does not halt. |
| **Decision** | `agents.py:decision` | `worker/pipeline/prompts/decision.py`. Synthesizes outputs. Validated by `_validate_decision_proposal`. | Assigns proposed status: `approved`, `denied`, or `escalated`. |
| **Critic** | (Planner step) | Currently skipped in executable graph (`workflow.py`). | N/A. |
| **Explanation**| `agents.py:explanation` | `worker/pipeline/prompts/explanation.py`. Generates one customer-safe paragraph. | Falls back to deterministic safe message if LLM fails. |

## Human Review Kill Switch (`worker/pipeline/helper.py`)
- Evaluates `human_review_kill_switch` from settings. Defaults to `True` (fail-safe).
- When active, the worker inserts the case into the `review_queue` table:
  `INSERT INTO review_queue (order_id, decision, explanation, payload, status, created_at)` with status `pending`.
- Does **not** disburse refunds or mark returns finalized automatically.
