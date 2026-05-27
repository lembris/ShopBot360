import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import is_phone_allowed, normalize_phone
from app.database.models.shop import Shop
from app.engines.analytics import analytics_engine
from app.engines.debt import debt_engine
from app.engines.inventory import inventory_engine
from app.engines.pos import pos_engine
from app.engines.reports import report_engine
from app.parser.ai_fallback import ai_fallback_service
from app.parser.command_parser import CommandParser
from app.parser.intents import Intent
from app.schemas.parser import IntentResult, ParsedEntity
from app.services.cache import cache_service
from app.services.session import session_service
from app.services.tenant import resolve_user_by_phone
from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)
parser = CommandParser()

SESSION_CANCEL_WORDS = {"cancel", "stop", "exit", "quit", "acha", "futa", "bila"}

SALES_INTENTS = {Intent.SELL}
INVENTORY_INTENTS = {
    Intent.STOCK_ADD,
    Intent.RESTOCK,
    Intent.STOCK_ALL,
    Intent.NEW_PRODUCT,
    Intent.PRICE,
    Intent.DELETE,
}
REPORT_INTENTS = {Intent.REPORT_TODAY, Intent.REPORT_WEEK, Intent.TOP_PRODUCTS}
ANALYTICS_INTENTS = {Intent.PROFIT_TODAY, Intent.SALES_CUSTOMER}
DEBT_INTENTS = {Intent.DEBT, Intent.PAYMENT, Intent.CREDIT_REPORT}


class MessageHandler:
    async def handle_inbound(
        self,
        db: AsyncSession,
        *,
        from_phone: str,
        text: str,
        message_id: str | None = None,
    ) -> str:
        phone = normalize_phone(from_phone)
        settings = get_settings()

        if message_id and await cache_service.is_message_processed(message_id):
            return ""
        if not await cache_service.check_rate_limit(phone, settings.rate_limit_per_second):
            return "Too many messages. Please wait a moment."

        if not is_phone_allowed(phone):
            try:
                await resolve_user_by_phone(db, phone)
            except Exception:
                return "Unauthorized. Contact shop owner to register your number."

        user = await resolve_user_by_phone(db, phone)
        shop = await db.get(Shop, user.shop_id)
        if not shop:
            return "Shop not found."

        if message_id:
            await cache_service.mark_message_processed(message_id)

        session = await session_service.get(str(shop.id), phone)
        if session and session.get("pending_intent"):
            if text.strip().lower() in SESSION_CANCEL_WORDS:
                await session_service.clear(str(shop.id), phone)
                return "Sale cancelled. Send 'help' for commands."
            fresh_intent = parser.parse(text)
            if fresh_intent.intent != Intent.UNKNOWN and fresh_intent.confidence >= 0.6:
                await session_service.clear(str(shop.id), phone)
            else:
                return await self._continue_session(
                    db, shop, user, phone, text, session
                )

        intent = parser.parse(text)
        if (
            intent.intent == Intent.UNKNOWN
            and intent.confidence < settings.ai_confidence_threshold
            and not intent.clarification_prompt
        ):
            intent = await ai_fallback_service.parse(text)

        if intent.needs_clarification and intent.intent == Intent.SELL:
            await session_service.set(
                str(shop.id),
                phone,
                {
                    "pending_intent": Intent.SELL,
                    "product": intent.entities.product,
                    "step": "qty",
                },
            )
            return intent.clarification_prompt or "How many?"

        if (
            intent.intent == Intent.SELL
            and intent.entities.qty
            and not intent.entities.price
        ):
            await session_service.set(
                str(shop.id),
                phone,
                {
                    "pending_intent": Intent.SELL,
                    "product": intent.entities.product,
                    "qty": intent.entities.qty,
                    "step": "price",
                },
            )
            return "Price per item?"

        return await self._dispatch(
            db,
            shop_id=shop.id,
            user_id=user.id,
            role=user.role,
            currency=shop.currency,
            timezone=shop.timezone,
            intent=intent,
        )

    async def _continue_session(
        self,
        db: AsyncSession,
        shop: Shop,
        user,
        phone: str,
        text: str,
        session: dict,
    ) -> str:
        step = session.get("step")
        if step == "qty":
            try:
                qty = int(text.strip())
            except ValueError:
                return "Please send a number for quantity."
            session["qty"] = qty
            session["step"] = "price"
            await session_service.set(str(shop.id), phone, session)
            return "Price per item?"
        if step == "price":
            try:
                from decimal import Decimal

                price = Decimal(text.strip())
            except Exception:
                return "Please send a valid price."
            intent = IntentResult(
                intent=Intent.SELL,
                entities=ParsedEntity(
                    product=session.get("product"),
                    qty=session.get("qty"),
                    price=price,
                ),
            )
            await session_service.clear(str(shop.id), phone)
            return await self._dispatch(
                db,
                shop_id=shop.id,
                user_id=user.id,
                role=user.role,
                currency=shop.currency,
                timezone=shop.timezone,
                intent=intent,
            )
        await session_service.clear(str(shop.id), phone)
        return "Session expired. Please send your command again."

    async def _dispatch(
        self,
        db: AsyncSession,
        *,
        shop_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        currency: str,
        timezone: str,
        intent: IntentResult,
    ) -> str:
        if intent.intent == Intent.HELP:
            return (
                "Commands:\n"
                "• sell 2 soda 1500\n"
                "• stock add sugar 50\n"
                "• report today\n"
                "• debt john / paid john 5000\n"
                "• profit today"
            )

        if intent.intent in SALES_INTENTS:
            return await pos_engine.execute(
                db, shop_id=shop_id, user_id=user_id, role=role, intent=intent, currency=currency
            )
        if intent.intent in INVENTORY_INTENTS:
            return await inventory_engine.execute(
                db, shop_id=shop_id, user_id=user_id, role=role, intent=intent, currency=currency
            )
        if intent.intent in REPORT_INTENTS:
            return await report_engine.execute(
                db, shop_id=shop_id, role=role, intent=intent, timezone=timezone, currency=currency
            )
        if intent.intent in ANALYTICS_INTENTS:
            return await analytics_engine.execute(
                db, shop_id=shop_id, role=role, intent=intent, timezone=timezone, currency=currency
            )
        if intent.intent in DEBT_INTENTS:
            return await debt_engine.execute(
                db, shop_id=shop_id, user_id=user_id, role=role, intent=intent, currency=currency
            )

        return intent.clarification_prompt or "Unknown command. Send 'help' for options."


message_handler = MessageHandler()
