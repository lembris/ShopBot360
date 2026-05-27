from app.services.whatsapp_providers.factory import get_primary_provider
from app.services.whatsapp_providers.models import InboundMessage
from app.services.whatsapp_providers.router import WhatsAppRouter

whatsapp_router = WhatsAppRouter()

__all__ = ["InboundMessage", "WhatsAppRouter", "whatsapp_router", "get_primary_provider"]
