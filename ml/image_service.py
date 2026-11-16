import base64
import io
import json
from functools import lru_cache
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from PIL import ExifTags, Image
from backend.app.services.storage import download_image
from worker.pipeline.llm import image_model
from worker.pipeline.nodes.base import VisionAssessment

AI_DETECTOR_REPO = "haywoodsloan/ai-image-detector-deploy"
CLIP_MODEL_REPO = "openai/clip-vit-base-patch32"
VISION_SIMILARITY_MIN = 0.6
VISION_SIMILARITY_MAX = 0.75
AI_PROBABILITY_THRESHOLD = 0.5
AI_STANDARD_RESOLUTIONS = {
    (1024, 1024),
    (1024, 1536),
    (1536, 1024),
    (768, 1024),
    (1024, 768),
}


@lru_cache(maxsize=1)
def _image_detector():
    import torch
    from transformers import AutoImageProcessor, AutoModelForImageClassification

    processor = AutoImageProcessor.from_pretrained(AI_DETECTOR_REPO)
    model = AutoModelForImageClassification.from_pretrained(AI_DETECTOR_REPO)
    model.eval()
    return torch, processor, model


@lru_cache(maxsize=1)
def _clip_model():
    import torch
    from transformers import CLIPImageProcessor, CLIPModel

    processor = CLIPImageProcessor.from_pretrained(CLIP_MODEL_REPO)
    model = CLIPModel.from_pretrained(CLIP_MODEL_REPO)
    model.eval()
    return torch, processor, model


def _inspect_image(data: bytes) -> tuple[Image.Image, bool, list[str]]:
    with Image.open(io.BytesIO(data)) as source:
        source.load()
        image = source.convert("RGB")
        exif = source.getexif()
        exif_values_raw = dict(exif.items())
        exif_values_raw.update(exif.get_ifd(ExifTags.IFD.Exif))
        exif_values = {
            ExifTags.TAGS.get(tag_id, str(tag_id)): str(value).strip().lower()
            for tag_id, value in exif_values_raw.items()
        }

    metadata_flags: list[str] = []
    metadata_ai_flag = False
    software = exif_values.get("Software", "")
    ai_software_terms = (
        "midjourney",
        "stable diffusion",
        "stablediffusion",
        "dall-e",
        "dalle",
        "comfyui",
        "automatic1111",
        "generative",
    )
    if any(term in software for term in ai_software_terms):
        metadata_flags.append("AI-generation software identified in EXIF")
        metadata_ai_flag = True

    if image.size in AI_STANDARD_RESOLUTIONS:
        metadata_flags.append(
            f"resolution {image.width}x{image.height} matches a common AI output size"
        )

    if not exif_values:
        metadata_flags.append("EXIF metadata is absent")
    elif not any(
        exif_values.get(field)
        for field in ("Make", "Model", "DateTime", "DateTimeOriginal")
    ):
        metadata_flags.append("camera make/model and capture timestamp are absent")

    return image, metadata_ai_flag, metadata_flags


def _artificial_probability(image: Image.Image) -> float:
    torch, processor, model = _image_detector()
    inputs = processor(images=image, return_tensors="pt")
    with torch.inference_mode():
        probabilities = torch.softmax(model(**inputs).logits, dim=-1)[0]

    artificial_indexes = [
        int(index)
        for index, label in model.config.id2label.items()
        if any(
            term in label.casefold()
            for term in ("artificial", "synthetic", "fake", "ai")
        )
    ]
    if len(artificial_indexes) != 1:
        raise ValueError(
            "AI-image detector must expose exactly one artificial/fake class; "
            f"labels were {model.config.id2label}"
        )
    return float(probabilities[artificial_indexes[0]].item())


def _clip_similarity(return_image: Image.Image, catalog_image: Image.Image) -> float:
    torch, processor, model = _clip_model()
    inputs = processor(images=[return_image, catalog_image], return_tensors="pt")
    with torch.inference_mode():
        image_outputs = model.vision_model(pixel_values=inputs["pixel_values"])
        if image_outputs.pooler_output is None:
            raise TypeError("CLIP did not return pooled image features")
        embeddings = model.visual_projection(image_outputs.pooler_output)
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=-1)
        similarity = torch.sum(embeddings[0] * embeddings[1])
    return float(similarity.item())


def _analyze_return_images(
    photo_keys: list[str], catalog_image_key: str
) -> tuple[bytes, list[bytes], float, bool, list[str]]:
    catalog_bytes = download_image(catalog_image_key)
    catalog_image, _, _ = _inspect_image(catalog_bytes)
    photo_bytes: list[bytes] = []
    similarities: list[float] = []
    fake_detected = False
    forensic_notes: list[str] = []

    for photo_key in photo_keys:
        data = download_image(photo_key)
        image, metadata_flag, metadata_notes = _inspect_image(data)
        probability = _artificial_probability(image)
        similarity = _clip_similarity(image, catalog_image)
        photo_bytes.append(data)
        similarities.append(similarity)
        fake_detected = (
            fake_detected
            or metadata_flag
            or probability >= AI_PROBABILITY_THRESHOLD
        )
        forensic_notes.extend(
            f"Return image {len(photo_bytes)}: {note}" for note in metadata_notes
        )
        forensic_notes.append(
            f"Return image {len(photo_bytes)} artificial probability: {probability:.4f}"
        )

    return (
        catalog_bytes,
        photo_bytes,
        sum(similarities) / len(similarities),
        fake_detected,
        forensic_notes,
    )


def _image_data_url(data: bytes) -> str:
    with Image.open(io.BytesIO(data)) as source:
        image = source.convert("RGB")
        encoded = io.BytesIO()
        image.save(encoded, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(encoded.getvalue()).decode(
        "ascii"
    )


def _run_vision_assessment(
    catalog_bytes: bytes,
    photo_bytes: list[bytes],
    product_name: str,
    category: str,
    description: str,
    reason: str,
    forensic_notes: list[str],
) -> dict[str, Any]:
    from worker.pipeline.prompts.image import VISION_PROMPT

    text = (
        f"Catalog product: {product_name}\n"
        f"Category: {category}\n"
        f"Catalog description: {description}\n"
        f"Customer-stated return reason (unverified): {reason}\n"
        "Forensic pre-filter observations (not proof of AI generation): "
        f"{json.dumps(forensic_notes)}\n"
        "The first image is the catalog photo. The remaining images are "
        "customer return photos."
    )
    image_blocks = [
        {
            "type": "image_url",
            "image_url": {"url": _image_data_url(catalog_bytes)},
        }
    ]
    image_blocks.extend(
        {
            "type": "image_url",
            "image_url": {"url": _image_data_url(data)},
        }
        for data in photo_bytes
    )
    response = image_model().invoke(
        [
            SystemMessage(content=VISION_PROMPT),
            HumanMessage(content=[{"type": "text", "text": text}, *image_blocks]),
        ]
    )
    content = response.content
    if not isinstance(content, str):
        raise TypeError("Image vision model returned non-text content.")
    return VisionAssessment.model_validate_json(content).model_dump()


def analyze_image(
    photo_keys: list[str],
    catalog_image_key: str,
    product_name: str,
    category: str,
    description: str,
    reason: str,
) -> dict[str, Any]:
    catalog_bytes, photo_bytes, similarity, fake_detected, forensic_notes = (
        _analyze_return_images(photo_keys, catalog_image_key)
    )
    similarity = round(similarity, 4)
    vision_call: list[dict[str, Any]] = []
    if VISION_SIMILARITY_MIN <= similarity < VISION_SIMILARITY_MAX:
        vision_call.append(
            _run_vision_assessment(
                catalog_bytes,
                photo_bytes,
                product_name,
                category,
                description,
                reason,
                forensic_notes,
            )
        )
        match = vision_call[0]["plausible"] is True
    else:
        match = similarity >= VISION_SIMILARITY_MAX

    return {
        "match": match,
        "similarilty": similarity,
        "fake_probabilty": fake_detected,
        "vision_call": vision_call,
    }
