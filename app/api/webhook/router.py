import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.webhook.handlers import process_inbound_messages
from app.core.config import get_settings
from app.database.connection import get_db
from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("")
async def webhook_verify(request: Request):
    """Provider-specific GET verification (Meta / 360dialog)."""
    params = dict(request.query_params)
    challenge = whatsapp_service.verify_webhook_challenge(params)
    if challenge is not None:
        if isinstance(challenge, int):
            return Response(content=str(challenge), media_type="text/plain")
        return Response(content=str(challenge), media_type="text/plain")
    # Twilio/WATI often skip GET verify — return OK for health probes
    settings = get_settings()
    if settings.whatsapp_provider in ("twilio", "wati"):
        return {"status": "ok", "provider": settings.whatsapp_provider}
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def webhook_receive(request: Request, db: AsyncSession = Depends(get_db)):
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type:
        form_body = await request.form()
        form = {k: str(v) for k, v in form_body.items()}
        messages = whatsapp_service.parse_webhook(form=form, headers=dict(request.headers))
    else:
        payload = await request.json()
        logger.debug("Webhook payload: %s", payload)
        messages = whatsapp_service.parse_webhook(
            payload, headers=dict(request.headers)
        )

    await process_inbound_messages(db, messages)
    return {"status": "ok"}


@router.post("/twilio")
async def webhook_twilio(request: Request, db: AsyncSession = Depends(get_db)):
    """Explicit Twilio webhook URL (form-encoded)."""
    form_body = await request.form()
    form = {k: str(v) for k, v in form_body.items()}
    from app.services.whatsapp_providers.twilio import TwilioProvider

    messages = TwilioProvider().parse_webhook(form=form)
    await process_inbound_messages(db, messages)
    return {"status": "ok"}


@router.post("/wati")
async def webhook_wati(request: Request, db: AsyncSession = Depends(get_db)):
    """Explicit WATI webhook URL."""
    payload = await request.json()
    from app.services.whatsapp_providers.wati import WatiProvider

    messages = WatiProvider().parse_webhook(payload)
    await process_inbound_messages(db, messages)
    return {"status": "ok"}


@router.post("/dialog360")
async def webhook_dialog360(request: Request, db: AsyncSession = Depends(get_db)):
    """Explicit 360dialog webhook URL."""
    payload = await request.json()
    from app.services.whatsapp_providers.dialog360 import Dialog360Provider

    messages = Dialog360Provider().parse_webhook(payload)
    await process_inbound_messages(db, messages)
    return {"status": "ok"}
