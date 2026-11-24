# LangGraph Review Workflow & Worker Jobs

> Last verified against commit: `c39ba3f`

## ARQ Worker Execution (`worker/pipeline/`)
- **Entry point**: `worker/pipeline/workers.py:WorkerSettings`. Run via `make worker` or `uv run arq worker.pipeline.workers.WorkerSettings`.
- **Registered job**: `review_return(ctx: dict, return_id: str)` in `worker/pipeline/jobs.py`.
- **DB Connection**: Async `psycopg 3` pool initialized during ARQ startup (`worker/pipeline/db.py`). Uses raw SQL in `worker/pipeline/query.py`.
- **Customer email**: When automatic review is enabled, `review_return` sends the review message using `backend.app.services.mail.send` and the customer email loaded with the return context. Human-review cases do not receive an automated decision email.
- **Tracing**: Langfuse integration in `worker/pipeline/tracing.py`. Enabled if `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are provided. LLM-agent spans record the rendered prompt as input; non-LLM agent spans do not record the case payload as input.

## LLM Execution Modes
- **`LLM_MODE=live`** (default): Uses the configured primary provider and structured-output fallback, preserving worker behavior.
- **`LLM_MODE=mock`**: Uses deterministic responses from the selected `LLM_SCENARIO` (`low_risk`, `high_risk`, `suspicious`, or `defective_product`). `llm_failure`, `malformed_response`, and `decision_failure` are available to exercise failure paths.
- **`LLM_MODE=replay`**: Reads responses only from `LLM_REPLAY_FILE`; it never constructs a provider client or falls back to one. The JSON file shape is `{"scenarios":{"low_risk":{"intake":{...},"policy":{...},"behavior":{...},"decision":{...},"explanation":{...},"image":{...}}}}`. The `image` entry is raw vision-model content; structured agent entries use their existing Pydantic schemas. An entry such as `{"$error":"simulated timeout"}` raises `MockLLMFailure`.
- **`LLM_SCENARIO`** selects the mock/replay case and defaults to `low_risk`. Missing replay paths, scenarios, or agent responses fail explicitly.

The router in `worker/pipeline/llm.py` is the sole factory for structured chat and image-vision models. Both factories branch on `LLM_MODE` before provider initialization; the live fallback chain exists only in live mode. `MockLLM` implements the LangChain `Runnable` interface, validates structured responses with Pydantic, and returns `AIMessage` for raw vision responses.

Run the mock/replay workflow tests with `uv run --group worker --group dev pytest tests`. Tests execute the actual LangGraph nodes and isolate network-backed policy/image services and the database-backed CatBoost context at their service boundaries.

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
   +---> [Behavior Agent] (CatBoost risk model; always scheduled)
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
| **Planner** | `agents.py:planner` | Deterministic logic: schedules intake and policy; adds image check if photos exist; always schedules behavior. | None. |
| **Intake** | `agents.py:intake` | `worker/pipeline/prompts/intake.py`. Evaluates submission vs purchased product. | If `mismatch` or `missing_info`: stops workflow, sets `case.status = "denied"`. |
| **Policy** | `agents.py:policy` | `worker/pipeline/prompts/policy.py`. Queries Qdrant hybrid index. | If `eligible=false`: `denied`; if `unclear`: `in_review`. Both halt. |
| **Image** | `agents.py:image` | `worker/pipeline/prompts/image.py`. Calls `ml/image_service.py` (CLIP, AI detector, EXIF, vision model). | Exceptions recorded on case; does not halt. |
| **Behavior** | `agents.py:behavior` | `worker/pipeline/prompts/behavior.py`. Evaluates CatBoost tabular model via `ml/model_service.py`; its LLM summary uses the existing `ExplanationResult` message schema. | Exceptions recorded on case; does not halt. |
| **Decision** | `agents.py:decision` | `worker/pipeline/prompts/decision.py`. Synthesizes outputs. Validated by `_validate_decision_proposal`. | Assigns proposed status: `approved`, `denied`, or `escalated`. |
| **Critic** | (Planner step) | Currently skipped in executable graph (`workflow.py`). | N/A. |
| **Explanation**| `agents.py:explanation` | `worker/pipeline/prompts/explanation.py`. Generates one customer-safe paragraph. | Falls back to deterministic safe message if LLM fails. |

## Human Review Kill Switch (`worker/pipeline/helper.py`)
- Evaluates `human_review_kill_switch` from settings. Defaults to `True` (fail-safe).
- When active, the worker inserts the case into the `review_queue` table:
  `INSERT INTO review_queue (order_id, decision, explanation, payload, status, created_at)` with status `pending`.
- Does **not** disburse refunds or mark returns finalized automatically.
