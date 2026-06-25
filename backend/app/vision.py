import io
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import google.generativeai as genai
from PIL import Image
from fastapi import UploadFile

from app.config import (
    ALLOWED_IMAGE_TYPES,
    GEMINI_API_KEY,
    JSON_PATH,
    MAX_IMAGE_DIMENSIONS,
    MAX_IMAGE_SIZE_BYTES,
    UPLOAD_DIR,
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

with open(JSON_PATH, encoding="utf-8") as f:
    VEHICLE_CATALOG = json.load(f)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL = genai.GenerativeModel("gemini-1.5-flash")


async def validate_upload_file(upload_file: UploadFile) -> bytes:
    if upload_file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Unsupported image type.")

    contents = await upload_file.read()

    if not contents:
        raise ValueError("Empty image.")

    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise ValueError("Image exceeds 5MB.")

    return contents


def preprocess_image(contents: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    image.thumbnail(MAX_IMAGE_DIMENSIONS)
    return image


def save_image(image: Image.Image, slot: str) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = UPLOAD_DIR / f"{timestamp}_{slot}.jpg"
    image.save(path, "JPEG", quality=85)
    return path


async def analyze_images(uploads: Dict[str, UploadFile]):

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured.")

    if "main" not in uploads:
        raise ValueError("Main vehicle image is required.")

    main_file = uploads["main"]

    contents = await validate_upload_file(main_file)

    image = preprocess_image(contents)

    save_image(image, "main")

    prompt = """
    Identify this vehicle.

    Return ONLY valid JSON.

    Format:

    {
      "detected_brand": "",
      "detected_model": "",
      "detected_body_type": "",
      "detected_color": "",
      "confidence": 0
    }

    If unsure, provide best estimate.
    """

    response = MODEL.generate_content(
        [
            prompt,
            image
        ]
    )

    text = response.text.strip()

    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    try:
        result = json.loads(text)
    except Exception:
        result = {
            "detected_brand": None,
            "detected_model": None,
            "detected_body_type": None,
            "detected_color": None,
            "confidence": 0,
        }

    return {
        "detected_brand": result.get("detected_brand"),
        "detected_model": result.get("detected_model"),
        "detected_body_type": result.get("detected_body_type"),
        "detected_color": result.get("detected_color"),
        "estimated_year": None,
        "vehicle_category": result.get("detected_body_type"),
        "images": [
            {
                "slot": "main",
                "filename": main_file.filename,
                "content_type": main_file.content_type,
                "width": image.width,
                "height": image.height,
            }
        ],
    }