"""
Return-Request Pipeline (Steps 0–3)

This diagram shows the first stage of an AI pipeline that processes a customer’s return request and moves it toward an eligibility decision.

0. Data-Quality Gate (rule-based, no AI): Checks the item name, required photos, and product information. If the gate fails, the workflow ends immediately and returns the case with the failed gate result; it does not run later agents or change the case status.

1. Planner Agent: Uses deterministic code to select the evidence checks. It always schedules intake and policy checks, selects image analysis when a photo exists, and selects behavior analysis when customer history indicates prior returns or denials.

2. Intake Agent: Uses the configured chat model to assess the request against the order and product information already loaded into the case. It returns `match`, `mismatch`, or `missing_info`. A mismatch or missing-information result ends the workflow before policy or later agents run.

3. Policy Agent: Retrieves relevant policy content from the Qdrant-backed policy knowledge base and asks the configured chat model to assess eligibility. It returns `true`, `false`, or `unclear`. A `false` or `unclear` result ends the workflow before image, behavior, decision, or explanation agents run.

Next: If intake matches and policy eligibility is `true`, the workflow runs selected image and behavior checks, then creates a decision proposal and customer-safe explanation.

"""


"""
Return-Request Pipeline, Part 2 (Steps 4–8)

This diagram continues the pipeline from the earlier agents (Data-Quality Gate, Planner, Intake, Policy) and carries the case through to a final, customer-ready decision.

4. Image Agent (verify the photo): Runs only if a photo exists. It uses three checks:

A CLIP similarity check compares the customer’s photo with the catalog photo. A score of 0.75 or higher is a match, 0.6 to 0.75 is borderline, and below 0.6 is a mismatch.
A local AI-image detector sets the fake-photo flag at its configured probability threshold. EXIF generator metadata also sets the flag; missing EXIF and common AI output resolutions are recorded as forensic observations, not proof of generation.
A vision LLM (gpt-4o, with gpt-4o-mini fallback) is called only for borderline cases, to answer whether the photo plausibly shows the product.

5. Behavior Agent (check for risk patterns): Loads behavior features from the database, uses a locally run ML model to calculate a risk score from 0 to 1, and uses the configured chat model to write a summary.

6. Decision Agent (combine all signals): Takes the typed outputs recorded on the case and asks the configured `init_chat` model for one proposal. Deterministic validation overrides unsafe approvals, escalates missing or unclear evidence, and permits denial only for policy ineligibility supported by policy references. Approval requires confidence ≥ 0.80 and behavior risk ≤ 0.15; refunds over $250, linked-account signals, and mismatched or suspicious images are escalated. The proposal is recorded for review and never executes a refund or changes the final case status.

7. Critic Agent: A critic step is not currently executed by the workflow.

8. Explanation Agent (write the final message): Takes the recorded decision proposal and customer-safe summaries of the key agent results, then writes one concise plain-English paragraph shared with the customer, reviewer, and audit log. It does not expose internal risk signals, scores, or account links, and does not claim that a refund was issued or processing completed. If the language model fails or returns unsafe wording, it uses an outcome-specific safe template.

The executable sequence is implemented in `worker/pipeline/workflow.py` as `run_workflow(case)`. A failed gate, an intake `mismatch`/`missing_info`, or policy `false`/`unclear` ends the workflow immediately. Otherwise, it executes selected evidence agents, then decision and explanation. Evidence-agent exceptions are recorded and the workflow continues so the decision can account for missing results. The `review_return` worker job invokes this workflow and returns the enriched case without changing its final status or executing a refund.

## Langfuse tracing

The worker creates a root `return-review-workflow` span and a child span for every executed agent. Tracing is disabled unless both `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set. Configure the keys from your Langfuse Cloud project in the worker environment (for example, in the local `.env`, which must not be committed). Leave `LANGFUSE_BASE_URL` unset to use Langfuse Cloud. The worker flushes queued spans during shutdown.

Agent traces include the case input and agent output payloads, which may contain customer and return information. Use demo data or configure suitable access controls, retention, and redaction before enabling tracing with real customer data. Keep credentials out of tracked files.

Get the project keys from Langfuse Cloud’s project settings and place them in the worker environment:

```dotenv
LANGFUSE_PUBLIC_KEY=<your-project-public-key>
LANGFUSE_SECRET_KEY=<your-project-secret-key>
```

Restart the ReturnGuard worker after changing its environment. Do not put these credentials in tracked files.
"""