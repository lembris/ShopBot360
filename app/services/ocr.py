"""OCR receipt parsing (Phase 4)."""

import logging
import tempfile
from pathlib import Path

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OCRService:
    async def download_image(self, media_id: str) -> bytes | None:
        settings = get_settings()
        if not settings.whatsapp_token:
            return None
        url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{media_id}"
        headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
        async with httpx.AsyncClient() as client:
            meta = await client.get(url, headers=headers)
            meta.raise_for_status()
            media_url = meta.json().get("url")
            if not media_url:
                return None
            img = await client.get(media_url, headers=headers)
            img.raise_for_status()
            return img.content

    async def parse_receipt_image(self, media_id: str) -> str | None:
        data = await self.download_image(media_id)
        if not data:
            return None
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            return "OCR dependencies not installed (Pillow, pytesseract)."

        settings = get_settings()
        if settings.tesseract_cmd:
            import pytesseract as pt

            pt.pytesseract.tesseract_cmd = settings.tesseract_cmd

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            image = Image.open(path)
            text = pytesseract.image_to_string(image)
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if not lines:
                return "No text detected on receipt."
            preview = "\n".join(lines[:10])
            return (
                "Receipt draft (confirm items):\n"
                f"{preview}\n\n"
                "Reply with a sell command to record, e.g. sell 2 soda 1500"
            )
        except Exception as exc:
            logger.warning("OCR failed: %s", exc)
            return None
        finally:
            Path(path).unlink(missing_ok=True)


ocr_service = OCRService()
