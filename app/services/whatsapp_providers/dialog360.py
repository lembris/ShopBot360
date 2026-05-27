import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.whatsapp_providers.base import WhatsAppProvider
from app.services.whatsapp_providers.meta import MetaCloudProvider
from app.services.whatsapp_providers.models import InboundMessage

logger = logging.getLogger(__name__)


class Dialog360Provider(WhatsAppProvider):
    """
    360dialog — Meta BSP partner. Uses Cloud API-compatible webhooks;
    onboarding via 360dialog instead of direct Meta.
    https://docs.360dialog.com/
    """

    name = "dialog360"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._meta_parser = MetaCloudProvider()

    def is_configured(self) -> bool:
        return bool(self.settings.dialog360_api_key)

    @property
    def _base_url(self) -> str:
        return self.settings.dialog360_base_url.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "D360-API-KEY": self.settings.dialog360_api_key,
            "Content-Type": "application/json",
        }

    async def send_text(self, to_phone: str, body: str) -> dict[str, Any] | None:
        if not self.is_configured():
            logger.warning("360dialog not configured")
            return None

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone.lstrip("+"),
            "type": "text",
            "text": {"body": body},
        }
        url = f"{self._base_url}/messages"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self._headers)
            response.raise_for_status()
            return response.json()

    def parse_webhook(
        self,
        payload: dict[str, Any] | None = None,
        *,
        form: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[InboundMessage]:
        # 360dialog webhook payload matches Meta Cloud API structure
        return self._meta_parser.parse_webhook(payload, form=form, headers=headers)

    async def download_media(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> bytes | None:
        if not media_id or not self.is_configured():
            return None
        url = f"{self._base_url}/{media_id}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            meta = await client.get(url, headers=self._headers)
            meta.raise_for_status()
            download_url = meta.json().get("url")
            if not download_url:
                return None
            file_resp = await client.get(download_url, headers=self._headers)
            file_resp.raise_for_status()
            return file_resp.content

    def verify_webhook_challenge(self, query_params: dict[str, str]) -> str | int | None:
        return self._meta_parser.verify_webhook_challenge(query_params)
