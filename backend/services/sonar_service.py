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
        "You are Leviathan's expert sonar analysis assistant for commercial small-boat fishing operations. "
        "Analyze this sonar/fishfinder screenshot in detail.\n\n"
        "CONTEXT: This is for a solo or small-crew commercial fishing vessel using nets (gillnets, purse seines, cast nets) "
        "and other commercial gear. Focus on commercial viability, school size for netting, and efficient targeting.\n\n"
        "Provide a comprehensive analysis including:\n\n"
        "1. FISH DETECTION:\n"
        "   - Count all visible fish arches/marks. Note that it may just be a colored dot for a fish or a huge blob for a school of fish. If so, do your best to estimate, do not return 0.\n"
        "   - Identify fish size indicators (large arches = bigger fish, small marks = baitfish)\n"
        "   - Note suspended fish vs bottom-hugging fish\n"
        "   - Assess if school is large enough for commercial netting operations\n\n"
        "2. SCHOOL CHARACTERISTICS:\n"
        "   - Primary depth in feet where most fish are holding (this is the target depth for nets)\n"
        "   - Density: sparse (not worth setting nets), moderate (viable school), or dense (prime target)\n"
        "   - Horizontal width of school in feet (important for net deployment)\n"
        "   - School movement direction if discernible\n\n"
        "3. STRUCTURE & ENVIRONMENT:\n"
        "   - Bottom structure: flat/rocky/drop-off/ledge\n"
        "   - Bottom depth in feet (total water depth, important for avoiding snags)\n"
        "   - Thermocline presence and depth (temperature break where fish often stack)\n"
        "   - Water column features (baitfish balls, debris, etc.)\n\n"
        "4. COMMERCIAL FISHING INTELLIGENCE:\n"
        "   - Species likelihood based on depth, structure, and behavior\n"
        "   - Best commercial method (gillnet depth, purse seine deployment, cast net from deck)\n"
        "   - Optimal net deployment depth and approach\n"
        "   - Whether to set nets here or move to better marks\n"
        "   - Snag risk assessment based on bottom type\n\n"
        "Format your response EXACTLY as follows:\n"
        "FISH_ARCHES: <number>\n"
        "DEPTH: <feet where fish school is located>\n"
        "DENSITY: <sparse|moderate|dense>\n"
        "WIDTH: <feet>\n"
        "BOTTOM_STRUCTURE: <yes|no>\n"
        "BOTTOM_TYPE: <flat|rocky|drop-off|ledge|unknown>\n"
        "BOTTOM_DEPTH: <total water depth in feet>\n"
        "THERMOCLINE: <feet or none>\n"
        "FISH_SIZE: <small|medium|large|mixed>\n"
        "FISH_BEHAVIOR: <suspended|bottom|scattered|schooling>\n"
        "BAITFISH_PRESENT: <yes|no>\n"
        "SPECIES_GUESS: <likely species based on signals>\n"
        "CONFIDENCE: <0.0-1.0>\n"
        "RECOMMENDATION: <detailed 2-3 sentence action plan with specific net deployment depth, method, and whether to set or move>"
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

        # Parse structured response
        parsed = self._parse_sonar_response(response_text)

        return SonarResponse(
            depth=parsed.get("depth", 0),
            density=parsed.get("density", "unknown"),
            school_width=parsed.get("width", "unknown"),
            confidence=parsed.get("confidence", 0.5),
            recommendation=parsed.get("recommendation", response_text),
            detected_objects=DetectedObjects(
                fish_arches=parsed.get("fish_arches", 0),
                bottom_structure=parsed.get("bottom_structure", False),
                thermocline=parsed.get("thermocline", None),
            ),
            bottom_type=parsed.get("bottom_type"),
            bottom_depth=parsed.get("bottom_depth"),
            fish_size=parsed.get("fish_size"),
            fish_behavior=parsed.get("fish_behavior"),
            baitfish_present=parsed.get("baitfish_present"),
            species_guess=parsed.get("species_guess"),
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

    def _parse_sonar_response(self, response_text: str) -> Dict:
        """Parse structured sonar analysis from Gemini response."""
        parsed = {}
        lines = response_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "fish_arches":
                try:
                    parsed["fish_arches"] = int(value)
                except ValueError:
                    parsed["fish_arches"] = 0

            elif key == "depth":
                try:
                    # Extract numeric value (e.g., "45 feet" -> 45)
                    parsed["depth"] = int("".join(filter(str.isdigit, value.split()[0])))
                except (ValueError, IndexError):
                    parsed["depth"] = 0

            elif key == "density":
                value_lower = value.lower()
                if any(d in value_lower for d in ["sparse", "moderate", "dense"]):
                    parsed["density"] = value_lower.split()[0]
                else:
                    parsed["density"] = "unknown"

            elif key == "width":
                try:
                    parsed["width"] = value.split()[0] + " ft"
                except IndexError:
                    parsed["width"] = "unknown"

            elif key == "bottom_structure":
                parsed["bottom_structure"] = "yes" in value.lower()

            elif key == "bottom_type":
                parsed["bottom_type"] = value.lower()

            elif key == "bottom_depth":
                try:
                    parsed["bottom_depth"] = int("".join(filter(str.isdigit, value.split()[0])))
                except (ValueError, IndexError):
                    parsed["bottom_depth"] = 0

            elif key == "thermocline":
                if "none" in value.lower():
                    parsed["thermocline"] = None
                else:
                    try:
                        parsed["thermocline"] = int("".join(filter(str.isdigit, value.split()[0])))
                    except (ValueError, IndexError):
                        parsed["thermocline"] = None

            elif key == "fish_size":
                parsed["fish_size"] = value.lower()

            elif key == "fish_behavior":
                parsed["fish_behavior"] = value.lower()

            elif key == "baitfish_present":
                parsed["baitfish_present"] = "yes" in value.lower()

            elif key == "species_guess":
                parsed["species_guess"] = value

            elif key == "confidence":
                try:
                    parsed["confidence"] = float(value)
                except ValueError:
                    parsed["confidence"] = 0.5

            elif key == "recommendation":
                parsed["recommendation"] = value

        return parsed

    def _ensure_model(self) -> genai.GenerativeModel:
        if self._model is not None:
            return self._model

        api_key = os.getenv("GEMINI_API_KEY")
        _configure_gemini(api_key)

        self._model = genai.GenerativeModel(self._model_name)
        return self._model