import asyncio
import logging

from sqlalchemy import select

from app.database.connection import async_session_factory
from app.database.models.shop import Shop
from app.database.models.user import User
from app.engines.notifications import build_daily_report_message
from app.services.whatsapp import whatsapp_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_daily_reports() -> None:
    async with async_session_factory() as db:
        shops = (await db.execute(select(Shop))).scalars().all()
        for shop in shops:
            owners = (
                await db.execute(
                    select(User).where(User.shop_id == shop.id, User.role == "owner")
                )
            ).scalars().all()
            msg = await build_daily_report_message(
                db, shop.id, shop.timezone, shop.currency
            )
            for owner in owners:
                await whatsapp_service.send_text(owner.phone, msg)


@celery_app.task(name="app.workers.report_worker.send_daily_reports")
def send_daily_reports() -> None:
    asyncio.run(_run_daily_reports())
