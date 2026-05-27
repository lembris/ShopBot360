from abc import ABC, abstractmethod
from typing import Any

from app.services.whatsapp_providers.models import InboundMessage


class WhatsAppProvider(ABC):
    """Vendor-agnostic WhatsApp transport layer."""

    name: str = "base"

    @abstractmethod
    async def send_text(self, to_phone: str, body: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def parse_webhook(
        self,
        payload: dict[str, Any] | None = None,
        *,
        form: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[InboundMessage]:
        ...

    @abstractmethod
    async def download_media(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> bytes | None:
        ...

    def verify_webhook_challenge(self, query_params: dict[str, str]) -> str | int | None:
        """Return challenge for GET verification, or None if not supported."""
        return None

    def is_configured(self) -> bool:
        return True
