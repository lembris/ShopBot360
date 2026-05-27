import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.message_handler import message_handler
from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)


async def process_webhook_payload(db: AsyncSession, payload: dict) -> None:
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                from_phone = message.get("from", "")
                text = message.get("text", {}).get("body", "")
                message_id = message.get("id")
                reply = await message_handler.handle_inbound(
                    db,
                    from_phone=from_phone,
                    text=text,
                    message_id=message_id,
                )
                if reply:
                    await whatsapp_service.send_text(from_phone, reply)


async def process_voice_message(db: AsyncSession, from_phone: str, media_id: str) -> None:
    from app.parser.voice import voice_parser

    text = await voice_parser.transcribe_whatsapp_audio(media_id)
    if text:
        reply = await message_handler.handle_inbound(db, from_phone=from_phone, text=text)
        if reply:
            await whatsapp_service.send_text(from_phone, reply)


async def process_image_message(db: AsyncSession, from_phone: str, media_id: str) -> None:
    from app.services.ocr import ocr_service

    draft = await ocr_service.parse_receipt_image(media_id)
    reply = draft or "Could not read receipt image."
    await whatsapp_service.send_text(from_phone, reply)
