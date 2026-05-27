import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.webhook.handlers import (
    process_image_message,
    process_voice_message,
    process_webhook_payload,
)
from app.api.webhook.verify import verify_webhook
from app.database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("")
async def webhook_verify(request: Request):
    params = request.query_params
    return verify_webhook(
        params.get("hub.mode"),
        params.get("hub.verify_token"),
        params.get("hub.challenge"),
    )


@router.post("")
async def webhook_receive(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    logger.debug("Webhook payload: %s", payload)

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                msg_type = message.get("type")
                from_phone = message.get("from", "")
                if msg_type == "audio":
                    media_id = message.get("audio", {}).get("id")
                    if media_id:
                        await process_voice_message(db, from_phone, media_id)
                    continue
                if msg_type == "image":
                    media_id = message.get("image", {}).get("id")
                    if media_id:
                        await process_image_message(db, from_phone, media_id)
                    continue

    await process_webhook_payload(db, payload)
    return {"status": "ok"}
