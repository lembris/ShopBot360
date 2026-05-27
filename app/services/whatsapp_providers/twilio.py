import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.security import normalize_phone
from app.services.whatsapp_providers.base import WhatsAppProvider
from app.services.whatsapp_providers.models import InboundMessage

logger = logging.getLogger(__name__)


class TwilioProvider(WhatsAppProvider):
    """
    Twilio WhatsApp API — good option without direct Meta Business approval.
    Use Sandbox for development: https://www.twilio.com/docs/whatsapp/sandbox
    """

    name = "twilio"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(
            self.settings.twilio_account_sid
            and self.settings.twilio_auth_token
            and self.settings.twilio_whatsapp_from
        )

    def _format_whatsapp(self, phone: str) -> str:
        p = normalize_phone(phone)
        return f"whatsapp:{p}"

    async def send_text(self, to_phone: str, body: str) -> dict[str, Any] | None:
        if not self.is_configured():
            logger.warning("Twilio WhatsApp not configured")
            return None

        url = (
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{self.settings.twilio_account_sid}/Messages.json"
        )
        data = {
            "From": self.settings.twilio_whatsapp_from,
            "To": self._format_whatsapp(to_phone),
            "Body": body,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                data=data,
                auth=(self.settings.twilio_account_sid, self.settings.twilio_auth_token),
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
        if not form:
            return []

        from_raw = form.get("From", "")
        phone = from_raw.replace("whatsapp:", "").strip()
        body = form.get("Body", "")
        num_media = int(form.get("NumMedia", "0") or "0")

        if num_media > 0:
            media_url = form.get("MediaUrl0")
            media_type = form.get("MediaContentType0", "")
            if media_type.startswith("audio"):
                return [
                    InboundMessage(
                        from_phone=phone,
                        message_type="audio",
                        message_id=form.get("MessageSid"),
                        media_url=media_url,
                        raw=dict(form),
                    )
                ]
            if media_type.startswith("image"):
                return [
                    InboundMessage(
                        from_phone=phone,
                        message_type="image",
                        message_id=form.get("MessageSid"),
                        media_url=media_url,
                        raw=dict(form),
                    )
                ]

        if not body:
            return []

        return [
            InboundMessage(
                from_phone=phone,
                message_type="text",
                text=body,
                message_id=form.get("MessageSid"),
                raw=dict(form),
            )
        ]

    async def download_media(
        self,
        media_id: str | None = None,
        *,
        media_url: str | None = None,
    ) -> bytes | None:
        if not media_url or not self.is_configured():
            return None
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                media_url,
                auth=(self.settings.twilio_account_sid, self.settings.twilio_auth_token),
            )
            response.raise_for_status()
            return response.content
