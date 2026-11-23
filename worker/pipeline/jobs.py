import asyncio

from psycopg.types.json import Jsonb

from backend.app.services import mail
from worker.pipeline import dependency, db, helper
from worker.pipeline.logger import configure_logging, get_logger
from worker.pipeline.query import RETURN_REVIEW_UPDATE_QUERY
from worker.pipeline.sample_case import case
from worker.pipeline.workflow import run_workflow

logger = get_logger(__name__)


async def review_return(ctx: dict, return_id: str):
    logger.info("Processing return", extra={"return_id": return_id})

    if not ctx.get("db_pool"):
        logger.error(
            "Worker database pool is not initialized",
            extra={"return_id": return_id},
        )
        raise RuntimeError("Worker database pool is not initialized.")

    try:
        context = await helper.load_return_context(return_id)
    except helper.ReturnNotFound:
        logger.exception("Return not found", extra={"return_id": return_id})
        raise

    case = helper.build_case(context)
    logger.info(
        "Return case created",
        extra={"return_id": return_id, "case_id": case.case_id},
    )

    result = await run_workflow(case)
    result_case = result["case"]

    kill_switch_on = helper.is_kill_switch_on()
    status = "in_review" if kill_switch_on else result_case.status

    rows = await db._rows(
        RETURN_REVIEW_UPDATE_QUERY,
        {
            "ai_result": Jsonb(
                result_case.model_dump(mode="json")["agent_results"]
            ),
            "status": status,
            "return_id": return_id,
        },
    )
    if not rows:
        logger.error(
            "Could not persist return review results",
            extra={"return_id": return_id},
        )
        raise RuntimeError(f"Could not update return {return_id}.")

    # Kill switch ON -> always human review
    if kill_switch_on:
        logger.info(
            "Kill switch is ON, forcing human review",
            extra={"return_id": return_id},
        )
        human_review_message = helper.human_review_message(return_id)
        dependency.notify_reviewer(context["customer_email"], f"Action Required: Return {return_id} Needs Review", human_review_message)
        return {"status": "pending_human_review", "return_id": return_id}


    message = helper.customer_message(result)
    dependency.notify_reviewer(context["customer_email"], "Your return request has been reviewed", message)
    logger.info(
        "Return review completed",
        extra={"return_id": return_id, "final_status": result_case.status},
    )
    return {"status": status, "return_id": return_id}



async def main():
    configure_logging()
    ctx: dict = {}
    await db.startup(ctx)  # opens the pool, same as arq would
    try:
        # result = await predict_return_risk(ctx, "e23f609f-8a52-43c1-8364-4c6832e8ced0")
        result = await run_workflow(case)
        logger.info(
            "Sample workflow completed",
            extra={
                "case_id": result["case"].case_id,
                "final_status": result["case"].status,
            },
        )

    finally:
        await db.shutdown(ctx)  # closes the pool cleanly


if __name__ == "__main__":
    asyncio.run(main())


# uv run python -m worker.pipeline.jobs
