import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.whatsapp_providers.base import WhatsAppProvider
from app.services.whatsapp_providers.models import InboundMessage

logger = logging.getLogger(__name__)


class MetaCloudProvider(WhatsAppProvider):
    name = "meta"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.whatsapp_token and self.settings.whatsapp_phone_number_id)

    @property
    def _messages_url(self) -> str:
        return (
            f"https://graph.facebook.com/{self.settings.whatsapp_api_version}"
            f"/{self.settings.whatsapp_phone_number_id}/messages"
        )

    async def send_text(self, to_phone: str, body: str) -> dict[str, Any] | None:
        if not self.is_configured():
            logger.warning("Meta WhatsApp not configured")
            return None

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone.lstrip("+"),
            "type": "text",
            "text": {"body": body},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._messages_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def parse_webhook(
        self,
        payload: dict[str, Any] | None = None,
        *,
        form: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[InboundMessage]:
        messages: list[InboundMessage] = []
        if not payload:
            return messages

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    msg_type = msg.get("type", "text")
                    inbound = InboundMessage(
                        from_phone=msg.get("from", ""),
                        message_type=msg_type,
                        message_id=msg.get("id"),
                        raw=msg,
                    )
                    if msg_type == "text":
                        inbound.text = msg.get("text", {}).get("body", "")
                    elif msg_type == "audio":
                        inbound.media_id = msg.get("audio", {}).get("id")
                    elif msg_type == "image":
                        inbound.media_id = msg.get("image", {}).get("id")
                    messages.append(inbound)
        return messages

    async def download_media(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> bytes | None:
        if not media_id or not self.is_configured():
            return None
        url = f"https://graph.facebook.com/{self.settings.whatsapp_api_version}/{media_id}"
        headers = {"Authorization": f"Bearer {self.settings.whatsapp_token}"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            meta = await client.get(url, headers=headers)
            meta.raise_for_status()
            download_url = meta.json().get("url")
            if not download_url:
                return None
            file_resp = await client.get(download_url, headers=headers)
            file_resp.raise_for_status()
            return file_resp.content

    def verify_webhook_challenge(self, query_params: dict[str, str]) -> str | int | None:
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")
        if mode == "subscribe" and token == self.settings.whatsapp_verify_token:
            return int(challenge) if challenge and challenge.isdigit() else challenge
        return None
