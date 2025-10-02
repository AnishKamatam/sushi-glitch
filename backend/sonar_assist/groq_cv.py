"""Groq vision model integration for sonar analysis."""

import asyncio
import base64
import io
import logging
import os
from typing import Dict, Optional

import aiohttp
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class GroqCV:
    """Client for Groq's free-tier vision model."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 10,
    ):
        """
        Initialize Groq CV client.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model_id: Model identifier (defaults to llama-3.2-90b-vision-preview)
            endpoint: API endpoint URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model_id = model_id or "llama-3.2-90b-vision-preview"
        self.endpoint = endpoint or "https://api.groq.com/openai/v1/chat/completions"
        self.timeout = timeout
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("Groq API key not found. Vision analysis will be disabled.")

    def _encode_frame(self, frame_bgr: np.ndarray, max_size: int = 512) -> str:
        """
        Encode frame to base64 JPEG with resizing.

        Args:
            frame_bgr: OpenCV BGR frame
            max_size: Maximum dimension size

        Returns:
            Base64 encoded JPEG string with data URI prefix
        """
        # Resize if needed
        h, w = frame_bgr.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            frame_bgr = cv2.resize(frame_bgr, (new_w, new_h))

        # Convert to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Encode to JPEG
        pil_image = Image.fromarray(frame_rgb)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        # Base64 encode
        b64_str = base64.b64encode(buffer.read()).decode('utf-8')

        return f"data:image/jpeg;base64,{b64_str}"

    async def analyze(
        self,
        frame_bgr: np.ndarray,
        crop: Optional[tuple] = None,
    ) -> Dict:
        """
        Analyze sonar frame using Groq vision model.

        Args:
            frame_bgr: OpenCV BGR frame
            crop: Optional (x, y, w, h) crop region

        Returns:
            Dictionary with keys:
                - class: 'school', 'debris', 'thermocline', or 'unknown'
                - confidence: 0.0-1.0
                - boxes: Optional list of [x1, y1, x2, y2, score]
                - reasoning: Brief explanation
        """
        if not self.enabled:
            return {
                "class": "unknown",
                "confidence": 0.0,
                "boxes": [],
                "reasoning": "Groq API key not configured"
            }

        # Crop if specified
        if crop:
            x, y, w, h = crop
            frame_bgr = frame_bgr[y:y+h, x:x+w].copy()

        # Encode frame
        try:
            image_data_uri = self._encode_frame(frame_bgr)
        except Exception as e:
            logger.error(f"Failed to encode frame: {e}")
            return {
                "class": "unknown",
                "confidence": 0.0,
                "boxes": [],
                "reasoning": f"Encoding error: {e}"
            }

        # Build prompt
        prompt = """Analyze this sonar/fishfinder image and classify what you see.

Focus on identifying:
- **school**: Clear fish school or multiple fish arches (bright clustered marks)
- **debris**: Scattered objects, likely non-fish (vegetation, structure fragments)
- **thermocline**: Horizontal band/layer (temperature boundary)
- **unknown**: Unclear or empty

Respond in this exact format:
CLASS: <school|debris|thermocline|unknown>
CONFIDENCE: <0.0-1.0>
REASONING: <brief 1-sentence explanation>

Be conservative with fish classifications - only say "school" if you see clear arches or clusters."""

        # Build request payload
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_uri}}
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.3,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Make request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Groq API error {response.status}: {error_text}")
                        return {
                            "class": "unknown",
                            "confidence": 0.0,
                            "boxes": [],
                            "reasoning": f"API error {response.status}"
                        }

                    result = await response.json()

        except asyncio.TimeoutError:
            logger.warning("Groq API request timed out")
            return {
                "class": "unknown",
                "confidence": 0.0,
                "boxes": [],
                "reasoning": "Request timeout"
            }
        except Exception as e:
            logger.error(f"Groq API request failed: {e}")
            return {
                "class": "unknown",
                "confidence": 0.0,
                "boxes": [],
                "reasoning": f"Request error: {e}"
            }

        # Parse response
        try:
            content = result["choices"][0]["message"]["content"]
            return self._parse_response(content)
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse Groq response: {e}")
            return {
                "class": "unknown",
                "confidence": 0.0,
                "boxes": [],
                "reasoning": "Parse error"
            }

    def _parse_response(self, content: str) -> Dict:
        """
        Parse structured response from model.

        Args:
            content: Model response text

        Returns:
            Parsed dictionary
        """
        result = {
            "class": "unknown",
            "confidence": 0.0,
            "boxes": [],
            "reasoning": ""
        }

        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "class":
                value_lower = value.lower()
                if value_lower in ["school", "debris", "thermocline", "unknown"]:
                    result["class"] = value_lower

            elif key == "confidence":
                try:
                    conf = float(value)
                    result["confidence"] = max(0.0, min(1.0, conf))
                except ValueError:
                    pass

            elif key == "reasoning":
                result["reasoning"] = value

        return result

    def should_query(
        self,
        frame_count: int,
        sample_rate_hz: float,
        fps: float,
        cv_confidence: Optional[float] = None,
        ambiguity_threshold: float = 0.5,
    ) -> bool:
        """
        Determine if we should query Groq on this frame.

        Args:
            frame_count: Current frame number
            sample_rate_hz: Target Groq query rate (e.g., 1 Hz = once per second)
            fps: Current processing FPS
            cv_confidence: Classical CV confidence (0-1), if available
            ambiguity_threshold: Query if CV confidence below this

        Returns:
            True if should query Groq
        """
        if not self.enabled:
            return False

        # Sampled queries: check frame count
        frames_between_samples = int(fps / sample_rate_hz) if sample_rate_hz > 0 else float('inf')
        is_sample_frame = (frame_count % max(1, frames_between_samples)) == 0

        # Also query on ambiguous detections
        is_ambiguous = cv_confidence is not None and cv_confidence < ambiguity_threshold

        return is_sample_frame or is_ambiguous


async def test_groq_cv():
    """Test Groq CV client with a synthetic frame."""
    # Create test frame
    test_frame = np.zeros((600, 800, 3), dtype=np.uint8)
    cv2.putText(
        test_frame, "TEST SONAR", (300, 300),
        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3
    )
    cv2.circle(test_frame, (400, 400), 50, (200, 200, 200), -1)

    client = GroqCV()

    if not client.enabled:
        print("Groq API key not configured. Skipping test.")
        return

    print("Testing Groq CV analysis...")
    result = await client.analyze(test_frame)

    print(f"\nResult:")
    print(f"  Class: {result['class']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Reasoning: {result['reasoning']}")


if __name__ == "__main__":
    asyncio.run(test_groq_cv())
