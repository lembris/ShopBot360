import asyncio
import logging

from sqlalchemy import select

from app.database.connection import async_session_factory
from app.database.models.product import Product
from app.database.models.shop import Shop
from app.database.models.user import User
from app.engines.notifications import format_low_stock_alert
from app.services.whatsapp import whatsapp_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _check_low_stock() -> None:
    async with async_session_factory() as db:
        shops = (await db.execute(select(Shop))).scalars().all()
        for shop in shops:
            low = (
                await db.execute(
                    select(Product).where(
                        Product.shop_id == shop.id,
                        Product.is_active.is_(True),
                        Product.stock_qty <= Product.reorder_at,
                    )
                )
            ).scalars().all()
            if not low:
                continue
            alert = format_low_stock_alert([(p.name, p.stock_qty) for p in low])
            owners = (
                await db.execute(
                    select(User).where(User.shop_id == shop.id, User.role == "owner")
                )
            ).scalars().all()
            for owner in owners:
                await whatsapp_service.send_text(owner.phone, alert)


@celery_app.task(name="app.workers.low_stock_worker.check_low_stock")
def check_low_stock() -> None:
    asyncio.run(_check_low_stock())
