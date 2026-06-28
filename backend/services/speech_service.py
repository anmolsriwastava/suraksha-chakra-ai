
"""
Speech-to-Text Service

Primary: Sarvam AI — built for Indian languages, handles
  Bhojpuri, Awadhi, Maithili much better than Whisper.

Fallback: Groq Whisper Large v3.

Input: audio file bytes
Output: transcribed text (str)
"""

import logging
import tempfile
import os

import httpx
from groq import Groq

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SUPPORTED_LANGUAGES = ["hi-IN", "bho-IN", "mai-IN"]  # Hindi, Bhojpuri, Maithili


async def transcribe_audio(audio_bytes: bytes, language_hint: str = "hi-IN") -> str:
    """
    Transcribe audio bytes to text.

    Tries Sarvam AI first (better Indian language support).
    Falls back to Groq Whisper if Sarvam is unavailable or key not set.

    Returns the transcribed string. Raises RuntimeError if both fail.
    """
    if settings.sarvam_api_key:
        try:
            return await _transcribe_with_sarvam(audio_bytes, language_hint)
        except Exception as e:
            logger.warning(f"Sarvam AI failed: {e}. Falling back to Groq Whisper.")

    return await _transcribe_with_groq(audio_bytes)


async def _transcribe_with_sarvam(audio_bytes: bytes, language: str) -> str:
    """Call Sarvam AI transcription API."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            SARVAM_STT_URL,
            headers={"api-subscription-key": settings.sarvam_api_key},
            files={"file": ("audio.ogg", audio_bytes, "audio/ogg")},
            data={
                "language_code": language,
                "model": "saarika:v1",
            },
        )

        response.raise_for_status()

        result = response.json()
        transcript = result.get("transcript", "").strip()

        if not transcript:
            raise ValueError("Sarvam returned empty transcript")

        logger.info(f"Sarvam transcript: {transcript[:80]}...")
        return transcript


async def _transcribe_with_groq(audio_bytes: bytes) -> str:
    """
    Fallback: Groq Whisper Large v3.

    Groq requires a file object, so we write the bytes to a
    temporary .ogg file before uploading.
    """

    client = Groq(api_key=settings.groq_api_key)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                language="hi",
                response_format="json",
                temperature=0,
            )

        transcript = result.text.strip()

        logger.info(f"Groq Whisper transcript: {transcript[:80]}...")

        return transcript

    finally:
        os.unlink(tmp_path)
