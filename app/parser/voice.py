"""Voice note parsing via Whisper (Phase 4)."""

import logging
import tempfile
from pathlib import Path

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class VoiceParser:
    async def download_media(self, media_id: str) -> bytes | None:
        settings = get_settings()
        if not settings.whatsapp_token:
            return None
        url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/{media_id}"
        )
        headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
        async with httpx.AsyncClient() as client:
            meta = await client.get(url, headers=headers)
            meta.raise_for_status()
            media_url = meta.json().get("url")
            if not media_url:
                return None
            audio = await client.get(media_url, headers=headers)
            audio.raise_for_status()
            return audio.content

    async def transcribe_whatsapp_audio(self, media_id: str) -> str | None:
        data = await self.download_media(media_id)
        if not data:
            return None
        try:
            return await self._transcribe_bytes(data)
        except Exception as exc:
            logger.warning("Voice transcription failed: %s", exc)
            return None

    async def _transcribe_bytes(self, audio_bytes: bytes) -> str | None:
        try:
            import whisper  # type: ignore
        except ImportError:
            logger.warning("openai-whisper not installed; voice parsing unavailable")
            return None

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(audio_bytes)
            path = f.name
        try:
            model = whisper.load_model("base")
            result = model.transcribe(path, language=None)
            return (result.get("text") or "").strip()
        finally:
            Path(path).unlink(missing_ok=True)


voice_parser = VoiceParser()
