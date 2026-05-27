import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def _base_url(self) -> str:
        return (
            f"https://graph.facebook.com/{self.settings.whatsapp_api_version}"
            f"/{self.settings.whatsapp_phone_number_id}/messages"
        )

    async def send_text(self, to_phone: str, body: str) -> dict | None:
        if not self.settings.whatsapp_token:
            logger.warning("WHATSAPP_TOKEN not set; message not sent: %s", body[:80])
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
            response = await client.post(self._base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


whatsapp_service = WhatsAppService()
