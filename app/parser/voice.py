"""Voice note parsing via Whisper (Phase 4)."""

import logging
import tempfile
from pathlib import Path

from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)


class VoiceParser:
    async def download_media(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> bytes | None:
        return await whatsapp_service.download_media(media_id, media_url=media_url)

    async def transcribe_whatsapp_audio(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> str | None:
        data = await self.download_media(media_id, media_url=media_url)
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
