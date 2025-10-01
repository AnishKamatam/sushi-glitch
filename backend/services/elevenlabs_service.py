"""Utility wrapper around the ElevenLabs Text-to-Speech API."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from elevenlabs import ElevenLabs


logger = logging.getLogger(__name__)

DEFAULT_PLACEHOLDER_API_KEY = "ELEVENLABS_API_KEY_PLACEHOLDER"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"


class ElevenLabsService:
    """Lightweight ElevenLabs Text-to-Speech client wrapper."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> None:
        self._api_key = (
            api_key
            or os.getenv("ELEVENLABS_API_KEY")
            or DEFAULT_PLACEHOLDER_API_KEY
        )

        if self._api_key == DEFAULT_PLACEHOLDER_API_KEY:
            logger.warning(
                "Using placeholder ElevenLabs API key. Replace with a real key via the environment."
            )

        self._model_id = model_id or os.getenv("ELEVENLABS_MODEL", DEFAULT_MODEL_ID)
        self._client = ElevenLabs(api_key=self._api_key)

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        *,
        model_id: Optional[str] = None,
        optimize_streaming_latency: Optional[int] = None,
        output_format: Optional[str] = None,
    ) -> bytes:
        """Return audio bytes for the given text and voice id."""

        return await asyncio.to_thread(
            self._synthesize_speech,
            text,
            voice_id,
            model_id,
            optimize_streaming_latency,
            output_format,
        )

    def _synthesize_speech(
        self,
        text: str,
        voice_id: str,
        model_id: Optional[str],
        optimize_streaming_latency: Optional[int],
        output_format: Optional[str],
    ) -> bytes:
        params: Dict[str, Any] = {
            "voice_id": voice_id,
            "model_id": model_id or self._model_id,
            "text": text,
        }

        if optimize_streaming_latency is not None:
            params["optimize_streaming_latency"] = optimize_streaming_latency

        if output_format is not None:
            params["output_format"] = output_format

        response = self._client.text_to_speech.convert(**params)

        if isinstance(response, bytes):
            audio_bytes = response
        else:
            audio_chunks: List[bytes] = []
            for chunk in response:
                if isinstance(chunk, bytes):
                    audio_chunks.append(chunk)
                elif hasattr(chunk, "audio"):
                    audio_chunks.append(chunk.audio)
                else:
                    logger.debug("Ignoring unexpected ElevenLabs chunk type: %r", chunk)

            audio_bytes = b"".join(audio_chunks)

        if not audio_bytes:
            raise RuntimeError("Received empty audio payload from ElevenLabs")

        return audio_bytes

    async def list_voices(self) -> List[Dict[str, Any]]:
        """Return metadata for voices available to the account."""

        return await asyncio.to_thread(self._list_voices)

    def _list_voices(self) -> List[Dict[str, Any]]:
        voices = self._client.voices.get_all()

        voice_entries: List[Dict[str, Any]] = []
        for voice in voices:
            voice_entries.append(
                {
                    "voice_id": getattr(voice, "voice_id", None),
                    "name": getattr(voice, "name", None),
                    "labels": getattr(voice, "labels", None),
                    "description": getattr(voice, "description", None),
                }
            )

        return voice_entries

