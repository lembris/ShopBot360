import logging

from app.core.config import get_settings
from app.services.whatsapp_providers.base import WhatsAppProvider
from app.services.whatsapp_providers.dialog360 import Dialog360Provider
from app.services.whatsapp_providers.meta import MetaCloudProvider
from app.services.whatsapp_providers.twilio import TwilioProvider
from app.services.whatsapp_providers.wati import WatiProvider

logger = logging.getLogger(__name__)

_PROVIDERS: dict[str, type[WhatsAppProvider]] = {
    "meta": MetaCloudProvider,
    "twilio": TwilioProvider,
    "dialog360": Dialog360Provider,
    "360dialog": Dialog360Provider,
    "wati": WatiProvider,
}


def create_provider(name: str) -> WhatsAppProvider:
    key = name.strip().lower()
    cls = _PROVIDERS.get(key)
    if not cls:
        raise ValueError(f"Unknown WhatsApp provider: {name}. Choose: {', '.join(_PROVIDERS)}")
    return cls()


def get_configured_providers() -> list[WhatsAppProvider]:
    """Primary provider first, then fallbacks that are configured."""
    settings = get_settings()
    names = [settings.whatsapp_provider, *settings.whatsapp_fallback_providers]
    seen: set[str] = set()
    providers: list[WhatsAppProvider] = []

    for name in names:
        key = name.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            provider = create_provider(key)
            if provider.is_configured():
                providers.append(provider)
            else:
                logger.debug("WhatsApp provider %s skipped (not configured)", key)
        except ValueError as exc:
            logger.warning("%s", exc)

    return providers


def get_primary_provider() -> WhatsAppProvider:
    providers = get_configured_providers()
    if not providers:
        settings = get_settings()
        return create_provider(settings.whatsapp_provider)
    return providers[0]
