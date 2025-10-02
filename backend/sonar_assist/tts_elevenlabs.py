"""ElevenLabs Text-to-Speech integration for voice cues."""

import asyncio
import logging
import os
import tempfile
import time
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# Try to import audio playback library
try:
    import simpleaudio as sa
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("simpleaudio not available. Voice output will be disabled. Install with: pip install simpleaudio")


class TTSElevenLabs:
    """Async ElevenLabs TTS client for low-latency voice cues."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        """
        Initialize ElevenLabs TTS client.

        Args:
            api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env var)
            voice_id: Voice ID (defaults to ELEVENLABS_VOICE_ID or Bill voice)
            model_id: Model ID (defaults to eleven_multilingual_v2)
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "pqHfZKP75CvOlQylNhV4")
        self.model_id = model_id or os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self.enabled = bool(self.api_key) and AUDIO_AVAILABLE

        if not self.api_key:
            logger.warning("ElevenLabs API key not found. Voice output will be disabled.")
        if not AUDIO_AVAILABLE:
            logger.warning("Audio playback not available.")

        self.last_spoken = {}  # text -> timestamp for debouncing
        self.current_playback = None

    async def speak(
        self,
        text: str,
        debounce_sec: float = 2.5,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> bool:
        """
        Speak text using ElevenLabs TTS.

        Args:
            text: Text to speak
            debounce_sec: Minimum seconds between identical messages
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity boost (0-1)

        Returns:
            True if spoken successfully, False otherwise
        """
        if not self.enabled:
            # Fallback: print to console
            print(f"[VOICE] {text}")
            return False

        # Debounce identical messages
        now = time.time()
        if text in self.last_spoken:
            if now - self.last_spoken[text] < debounce_sec:
                logger.debug(f"Debounced duplicate message: {text}")
                return False

        self.last_spoken[text] = now

        # Generate audio
        try:
            audio_bytes = await self._generate_audio(text, stability, similarity_boost)
        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            print(f"[VOICE] {text}")  # Fallback
            return False

        # Play audio
        try:
            await self._play_audio(audio_bytes)
            logger.info(f"Spoke: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            print(f"[VOICE] {text}")  # Fallback
            return False

    async def _generate_audio(
        self,
        text: str,
        stability: float,
        similarity_boost: float,
    ) -> bytes:
        """
        Generate audio from text via ElevenLabs API.

        Args:
            text: Text to synthesize
            stability: Voice stability
            similarity_boost: Voice similarity boost

        Returns:
            MP3 audio bytes
        """
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }

        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=15) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"ElevenLabs API error {response.status}: {error_text}")

                return await response.read()

    async def _play_audio(self, audio_bytes: bytes):
        """
        Play MP3 audio bytes.

        Args:
            audio_bytes: MP3 audio data
        """
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
            f.write(audio_bytes)

        try:
            # Convert MP3 to WAV for simpleaudio
            # Note: This requires ffmpeg. For production, use a proper audio library.
            # For now, we'll use a simple approach with subprocess
            import subprocess

            wav_path = temp_path.replace(".mp3", ".wav")

            # Try to use ffmpeg if available
            try:
                subprocess.run(
                    ["ffmpeg", "-i", temp_path, "-y", wav_path],
                    check=True,
                    capture_output=True
                )

                # Play WAV
                wave_obj = sa.WaveObject.from_wave_file(wav_path)
                play_obj = wave_obj.play()
                self.current_playback = play_obj

                # Wait for playback to finish
                await asyncio.to_thread(play_obj.wait_done)

                # Cleanup
                os.unlink(wav_path)

            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("ffmpeg not available. Falling back to text output.")
                raise RuntimeError("ffmpeg required for audio playback")

        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_path)
            except:
                pass

    def stop(self):
        """Stop current playback if any."""
        if self.current_playback:
            try:
                self.current_playback.stop()
            except:
                pass
            self.current_playback = None


class DebounceManager:
    """Helper to debounce similar messages."""

    def __init__(self, debounce_sec: float = 2.5, similarity_threshold: float = 0.8):
        """
        Initialize debounce manager.

        Args:
            debounce_sec: Minimum seconds between similar messages
            similarity_threshold: Similarity ratio to consider messages the same
        """
        self.debounce_sec = debounce_sec
        self.similarity_threshold = similarity_threshold
        self.last_message = ""
        self.last_time = 0

    def should_speak(self, message: str) -> bool:
        """
        Check if message should be spoken.

        Args:
            message: Message to check

        Returns:
            True if should speak
        """
        now = time.time()

        # Check time debounce
        if now - self.last_time < self.debounce_sec:
            # Check similarity
            if self._is_similar(message, self.last_message):
                return False

        self.last_message = message
        self.last_time = now
        return True

    def _is_similar(self, msg1: str, msg2: str) -> bool:
        """
        Check if two messages are similar.

        Args:
            msg1: First message
            msg2: Second message

        Returns:
            True if similar
        """
        if not msg1 or not msg2:
            return False

        # Simple similarity: check if key words match
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1 & words2
        union = words1 | words2

        similarity = len(intersection) / len(union)
        return similarity >= self.similarity_threshold


async def test_tts():
    """Test TTS client."""
    tts = TTSElevenLabs()

    if not tts.enabled:
        print("TTS not enabled. Check API key and audio library.")
        return

    print("Testing ElevenLabs TTS...")

    test_messages = [
        "Large, tight school around 44 feet. Drop to 44 and hold.",
        "School near 36 to 38 feet. Troll through 37 feet.",
        "Likely thermocline band. Ignore for now.",
    ]

    for msg in test_messages:
        print(f"\nSpeaking: {msg}")
        await tts.speak(msg)
        await asyncio.sleep(1)

    print("\nTTS test complete.")


if __name__ == "__main__":
    asyncio.run(test_tts())
