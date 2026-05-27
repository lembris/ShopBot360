from dataclasses import dataclass
from typing import Any


@dataclass
class InboundMessage:
    """Normalized inbound WhatsApp message from any provider."""

    from_phone: str
    message_type: str = "text"  # text, audio, image
    text: str | None = None
    message_id: str | None = None
    media_id: str | None = None
    media_url: str | None = None
    raw: dict[str, Any] | None = None
