import asyncio
import json
from functools import lru_cache
from typing import Any

import pandas as pd
from catboost import CatBoostClassifier
from redis.credentials import logger

from ml.model_service import load_model, risk_probability
from worker.pipeline import db, helper
from worker.pipeline.sample_case import case
from worker.pipeline.workflow import run_workflow


async def review_return(ctx: dict, return_id: str):
    logger.info("Processing return %s", return_id)

    if not ctx.get("db_pool"):
        raise RuntimeError("Worker database pool is not initialized.")

    try:
        context = await helper.load_return_context(return_id)
    except helper.ReturnNotFound:
        logger.error("Return %s not found", return_id)
        raise

    case = helper.build_case(context)
    logger.info("Case created: %s", case.case_id)
    return await run_workflow(case)


@lru_cache(maxsize=1)
def _risk_model() -> CatBoostClassifier:
    """Load the behavior model once per worker process."""
    return load_model()


async def predict_return_risk(ctx: dict, return_id: str) -> dict[str, Any]:
    """Fetch a return's ML features and return its predicted class probabilities."""
    if not ctx.get("db_pool"):
        raise RuntimeError("Worker database pool is not initialized.")

    context = await helper.load_ml_context(return_id)
    model = _risk_model()

    if model.feature_names_ is None:
        raise ValueError("The behavior model does not expose its feature names.")

    feature_names = list(model.feature_names_)
    missing_columns = [name for name in feature_names if name not in context]
    if missing_columns:
        raise ValueError(f"ML context is missing model features: {missing_columns}")

    missing_values = [name for name in feature_names if context[name] is None]
    if missing_values:
        raise ValueError(
            f"Cannot score return {return_id}; these features are unavailable: "
            f"{missing_values}"
        )

    features = pd.DataFrame(
        [{name: context[name] for name in feature_names}],
        columns=feature_names,
    )
    predictions = risk_probability(model=model, X=features)
    if len(predictions) != 1:
        raise RuntimeError(
            f"Expected one prediction for return {return_id}, got {len(predictions)}"
        )

    return {
        "return_id": return_id,
        "features": context,
        "prediction": predictions[0],
    }

async def main():
    ctx: dict = {}
    await db.startup(ctx)  # opens the pool, same as arq would
    try:
        # result = await predict_return_risk(ctx, "e23f609f-8a52-43c1-8364-4c6832e8ced0")
        # print(json.dumps(result, indent=2, default=str))
        result = await run_workflow(case)
        print(json.dumps(result, indent=2, default=str))

    finally:
        await db.shutdown(ctx)  # closes the pool cleanly
        print("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())


# uv run python -m worker.pipeline.jobs
