"""WhatsApp messaging facade — delegates to multi-vendor router."""

from app.services.whatsapp_providers import whatsapp_router

# Backward-compatible singleton used across the app
whatsapp_service = whatsapp_router
