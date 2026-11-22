# Machine Learning Services Specification

> Last verified against commit: `c39ba3f`

## Overview
The `ml/` package provides two standalone verification services: customer behavioral risk scoring and multi-modal image forensics.

## 1. Behavior Risk Model (`ml/model_service.py`)
- **Model Type**: CatBoost Classifier (`CatBoostClassifier`).
- **Artifact Path**: `ml/behaviour_risk_model.cbm`.
- **Target Classes**:
  - `0`: `legitimate` (risk score 0)
  - `1`: `policy_abuser` (risk weight 70)
  - `2`: `fraudulent_return` (risk weight 100)
  - `3`: `wardrobing` (risk weight 40)
- **Features Required (10 total)**:
  1. `return_rate_pct` (float)
  2. `customer_support_contacts` (int)
  3. `refund_to_order_ratio` (float)
  4. `previous_dispute_count` (int)
  5. `item_returned_opened` (int/bool)
  6. `multiple_accounts_flag` (int/bool)
  7. `refund_to_different_account` (int/bool)
  8. `refund_amount_requested_usd` (float)
  9. `return_reason` (string/category)
  10. `address_change_before_delivery` (int/bool)
- **Entry Points**:
  - `load_model()`: Loads the serialized model into memory.
  - `risk_probability(model, X)`: Returns class probabilities and the predicted top class.

## 2. Image Forensics & Vision Service (`ml/image_service.py`)
- **Entry point**: `analyze_image(...)`
- **Storage integration**: Uses `backend.app.services.storage.download_image` to fetch return and product photos from MinIO.
- **Forensic Checks**:
  1. **CLIP Visual Similarity**: Compares return photo with catalog product photo using `openai/clip-vit-base-patch32`. Thresholds: Match (>= 0.75), Borderline (0.60–0.75), Mismatch (< 0.60).
  2. **AI Generation Detector**: Evaluates image tensor against `haywoodsloan/ai-image-detector-deploy` (flags if probability > 0.50).
  3. **EXIF Metadata Inspection**: Scans for AI software tags (`midjourney`, `stable diffusion`, `dall-e`, `comfyui`), standard AI canvas resolutions (e.g., 1024x1024, 1536x1024), and missing camera hardware fields.
  4. **Vision LLM Fallback**: If CLIP similarity is borderline (0.60–0.75), queries vision LLM (`gpt-4o` with `gpt-4o-mini` fallback) to confirm product identity.
