import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.security import normalize_phone
from app.services.whatsapp_providers.base import WhatsAppProvider
from app.services.whatsapp_providers.models import InboundMessage

logger = logging.getLogger(__name__)


class WatiProvider(WhatsAppProvider):
    """
    WATI.io — popular for SMBs; easier onboarding than direct Meta in many regions.
    https://docs.wati.io/
    """

    name = "wati"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.wati_api_token and self.settings.wati_api_base_url)

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.settings.wati_api_token}"}

    def _phone_digits(self, phone: str) -> str:
        return normalize_phone(phone).lstrip("+")

    async def send_text(self, to_phone: str, body: str) -> dict[str, Any] | None:
        if not self.is_configured():
            logger.warning("WATI not configured")
            return None

        digits = self._phone_digits(to_phone)
        url = f"{self.settings.wati_api_base_url.rstrip('/')}/api/v1/sendSessionMessage/{digits}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self._headers,
                json={"messageText": body},
            )
            response.raise_for_status()
            return response.json()

    def parse_webhook(
        self,
        payload: dict[str, Any] | None = None,
        *,
        form: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[InboundMessage]:
        if not payload:
            return []

        messages: list[InboundMessage] = []

        # WATI sends various event types
        event_type = payload.get("eventType") or payload.get("type") or ""
        if event_type and "message" not in str(event_type).lower():
            return messages

        phone = (
            payload.get("waId")
            or payload.get("from")
            or payload.get("whatsappNumber")
            or ""
        )
        text = payload.get("text") or payload.get("messageText") or payload.get("body") or ""
        msg_id = payload.get("id") or payload.get("messageId")

        # Batch webhook wrapper
        if "messages" in payload and isinstance(payload["messages"], list):
            for item in payload["messages"]:
                messages.extend(
                    self.parse_webhook(item, form=form, headers=headers)
                )
            return messages

        if not phone:
            return messages

        media_url = payload.get("mediaUrl") or payload.get("data", {}).get("mediaUrl")
        if payload.get("type") == "audio" or payload.get("messageType") == "audio":
            return [
                InboundMessage(
                    from_phone=str(phone),
                    message_type="audio",
                    message_id=str(msg_id) if msg_id else None,
                    media_url=media_url,
                    raw=payload,
                )
            ]
        if payload.get("type") == "image" or payload.get("messageType") == "image":
            return [
                InboundMessage(
                    from_phone=str(phone),
                    message_type="image",
                    message_id=str(msg_id) if msg_id else None,
                    media_url=media_url,
                    raw=payload,
                )
            ]

        if text:
            messages.append(
                InboundMessage(
                    from_phone=str(phone),
                    message_type="text",
                    text=str(text),
                    message_id=str(msg_id) if msg_id else None,
                    raw=payload,
                )
            )
        return messages

    async def download_media(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> bytes | None:
        if not media_url:
            return None
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(media_url, headers=self._headers)
            response.raise_for_status()
            return response.content
