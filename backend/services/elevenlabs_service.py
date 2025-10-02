"""Utility wrapper around the ElevenLabs Text-to-Speech API."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play


logger = logging.getLogger(__name__)

class ElevenLabsService:
    """Lightweight ElevenLabs Text-to-Speech client wrapper."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> None:
        # Hackathon defaults - hardcoded for quick testing
        self._api_key = (
            api_key
            or os.getenv("ELEVENLABS_API_KEY")
            or "your_elevenlabs_api_key_here"  # Replace with actual key
        )

        if self._api_key == "your_elevenlabs_api_key_here":
            logger.warning(
                "Using placeholder ElevenLabs API key. Replace with a real key."
            )

        self._model_id = model_id or os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self._client = ElevenLabs(api_key=self._api_key)

    def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        *,
        model_id: Optional[str] = None,
        output_format: Optional[str] = "mp3_44100_128",
    ):
        """Return audio for the given text and voice id."""
        
        return self._client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id or self._model_id,
            output_format=output_format,
        )

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

def test_elevenlabs_service():
    """Test function to verify ElevenLabs service functionality."""
    load_dotenv()
    print("starting test...")
    service = ElevenLabsService()
    print("initialized service...")
    audio = service.synthesize_speech(
        text="The first move is what sets everything in motion.",
        voice_id="pqHfZKP75CvOlQylNhV4",
    )
    play(audio)


if __name__ == "__main__":
    test_elevenlabs_service()