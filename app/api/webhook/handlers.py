import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ShopBotError
from app.services.message_handler import message_handler
from app.services.whatsapp import whatsapp_service
from app.services.whatsapp_providers.models import InboundMessage

logger = logging.getLogger(__name__)


async def process_inbound_message(db: AsyncSession, msg: InboundMessage) -> None:
    """Route a normalized inbound message through business logic."""
    if msg.message_type == "audio":
        await process_voice_message(
            db, msg.from_phone, media_id=msg.media_id, media_url=msg.media_url
        )
        return
    if msg.message_type == "image":
        await process_image_message(
            db, msg.from_phone, media_id=msg.media_id, media_url=msg.media_url
        )
        return
    if msg.message_type == "text" and msg.text:
        try:
            reply = await message_handler.handle_inbound(
                db,
                from_phone=msg.from_phone,
                text=msg.text,
                message_id=msg.message_id,
            )
        except ShopBotError as exc:
            logger.warning("Command error for %s: %s", msg.from_phone, exc.message)
            reply = exc.message
        if reply:
            await whatsapp_service.send_text(msg.from_phone, reply)


async def process_inbound_messages(db: AsyncSession, messages: list[InboundMessage]) -> None:
    for msg in messages:
        await process_inbound_message(db, msg)


async def process_voice_message(
    db: AsyncSession,
    from_phone: str,
    *,
    media_id: str | None = None,
    media_url: str | None = None,
) -> None:
    from app.parser.voice import voice_parser

    text = await voice_parser.transcribe_whatsapp_audio(media_id, media_url=media_url)
    if text:
        reply = await message_handler.handle_inbound(db, from_phone=from_phone, text=text)
        if reply:
            await whatsapp_service.send_text(from_phone, reply)


async def process_image_message(
    db: AsyncSession,
    from_phone: str,
    *,
    media_id: str | None = None,
    media_url: str | None = None,
) -> None:
    from app.services.ocr import ocr_service

    draft = await ocr_service.parse_receipt_image(media_id, media_url=media_url)
    reply = draft or "Could not read receipt image."
    await whatsapp_service.send_text(from_phone, reply)
