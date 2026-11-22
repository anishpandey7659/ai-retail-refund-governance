# Machine Learning Agent Guide

## Responsibilities & Stack
- **Scope**: Customer behavioral risk classification and multi-modal return photo forensic verification.
- **Stack**: CatBoost, PyTorch, HuggingFace Transformers (CLIP, AI detector), Pillow, boto3.

## Key Directories & Entry Points
- `ml/model_service.py`: CatBoost classifier scoring (`risk_probability`, `load_model`).
- `ml/behaviour_risk_model.cbm`: Pre-trained CatBoost multi-class model weights.
- `ml/image_service.py`: Image forensics pipeline (`analyze_image`).

## Conventions & Rules
- The behavior model expects 10 tabular features matching `ML_CONTEXT_QUERY` in `worker/pipeline/query.py`.
- Download images via `backend.app.services.storage.download_image` rather than direct S3 calls.
- Image verification checks CLIP similarity (thresholds: 0.75 match, 0.60 mismatch) and AI generation probability (> 0.50).
- Model operations must run locally without unnecessary network requests.

## Testing & Execution
- Test ML model: `uv run python -m scripts.test_ml_model`.
- Test model context extraction: `uv run python -m scripts.test_model_context`.

## Docs to Read
- `docs/ml/SERVICES.md`, `docs/pipeline/WORKFLOW.md`.
