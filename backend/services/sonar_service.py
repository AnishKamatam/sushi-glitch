import asyncio
import base64
import logging
import os
from typing import Dict, List, Optional

import google.generativeai as genai

from models.schemas import DetectedObjects, SonarRequest, SonarResponse

logger = logging.getLogger(__name__)


def _configure_gemini(api_key: Optional[str]) -> None:
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to your environment or .env file."
        )

    if not getattr(_configure_gemini, "_configured", False):
        genai.configure(api_key=api_key)
        _configure_gemini._configured = True


def _build_prompt() -> str:
    return (
        "You are Leviathan's sonar freshness analyst. Given an uploaded deck or fish image, "
        "assess freshness. Respond in the following format:\n\n"
        "**FRESHNESS VERDICT:** <short, emphatic verdict>\n"
        "Justification: <one sentence with key cues you detected>."
    )


class SonarService:
    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self._model: Optional[genai.GenerativeModel] = None

    async def analyze_sonar(self, request: SonarRequest) -> SonarResponse:
        if not request.image:
            raise ValueError("Sonar image payload is required.")

        prompt = _build_prompt()
        image_parts = self._prepare_image_parts(request.image)

        response_text = await self._generate_content(prompt, image_parts)

        return SonarResponse(
            depth=0,
            density="unknown",
            school_width="unknown",
            confidence=0.0,
            recommendation=response_text,
            detected_objects=DetectedObjects(
                fish_arches=0,
                bottom_structure=False,
                thermocline=None,
            ),
        )

    async def _generate_content(self, prompt: str, image_parts: List[Dict[str, bytes]]) -> str:
        try:
            response = await asyncio.to_thread(
                self._ensure_model().generate_content,
                [prompt, *image_parts],
            )
        except Exception as exc:  # pragma: no cover - log unexpected API errors
            logger.exception("Gemini content generation failed")
            raise RuntimeError("Failed to generate sonar analysis") from exc

        if not response or not getattr(response, "text", None):
            logger.error("Gemini response missing text payload: %s", response)
            raise RuntimeError("Empty response from Gemini model")

        return response.text.strip()

    def _prepare_image_parts(self, image_data_uri: str) -> List[Dict[str, bytes]]:
        if image_data_uri.startswith("data:"):
            header, encoded = image_data_uri.split(",", 1)
            mime_type = header.split(";")[0].replace("data:", "") or "image/png"
        else:
            mime_type = "image/png"
            encoded = image_data_uri

        try:
            image_bytes = base64.b64decode(encoded)
        except Exception as exc:
            raise ValueError("Invalid base64 image payload") from exc

        return [
            {
                "mime_type": mime_type,
                "data": image_bytes,
            }
        ]

    def _ensure_model(self) -> genai.GenerativeModel:
        if self._model is not None:
            return self._model

        api_key = os.getenv("GEMINI_API_KEY")
        _configure_gemini(api_key)

        self._model = genai.GenerativeModel(self._model_name)
        return self._model