import logging
from typing import Any

import httpx

from app.services.whatsapp_providers.base import WhatsAppProvider
from app.services.whatsapp_providers.factory import get_configured_providers, get_primary_provider
from app.services.whatsapp_providers.models import InboundMessage

logger = logging.getLogger(__name__)


class WhatsAppRouter:
    """Send via primary provider; optional fallback chain on failure."""

    def __init__(self, providers: list[WhatsAppProvider] | None = None) -> None:
        self._providers = providers or get_configured_providers()

    @property
    def primary(self) -> WhatsAppProvider:
        if self._providers:
            return self._providers[0]
        return get_primary_provider()

    def all_providers(self) -> list[WhatsAppProvider]:
        return self._providers or [get_primary_provider()]

    async def send_text(self, to_phone: str, body: str) -> dict[str, Any] | None:
        errors: list[str] = []
        for provider in self.all_providers():
            try:
                result = await provider.send_text(to_phone, body)
                if result is not None:
                    logger.info("Sent via %s to %s", provider.name, to_phone)
                    return result
            except httpx.HTTPError as exc:
                msg = f"{provider.name}: {exc}"
                logger.warning("WhatsApp send failed (%s)", msg)
                errors.append(msg)
            except Exception as exc:
                msg = f"{provider.name}: {exc}"
                logger.exception("WhatsApp send error")
                errors.append(msg)

        if errors:
            logger.error("All WhatsApp providers failed: %s", "; ".join(errors))
        return None

    def parse_webhook(
        self,
        payload: dict[str, Any] | None = None,
        *,
        form: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[InboundMessage]:
        return self.primary.parse_webhook(payload, form=form, headers=headers)

    async def download_media(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> bytes | None:
        for provider in self.all_providers():
            try:
                data = await provider.download_media(media_id, media_url=media_url)
                if data:
                    return data
            except Exception as exc:
                logger.warning("Media download failed on %s: %s", provider.name, exc)
        return None

    def verify_webhook_challenge(self, query_params: dict[str, str]) -> str | int | None:
        return self.primary.verify_webhook_challenge(query_params)
