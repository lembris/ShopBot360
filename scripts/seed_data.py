"""Seed one shop with sample products."""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password, normalize_phone
from app.database.connection import async_session_factory
from app.database.transaction import transactional
from app.database.models.product import Product
from app.database.models.shop import Shop
from app.database.models.shop_phone import ShopPhoneNumber
from app.database.models.subscription import Subscription
from app.database.models.user import User
from app.core.constants import UserRole

SAMPLE_PRODUCTS = [
    ("Soda", Decimal("1500"), 50, Decimal("1000")),
    ("Sugar", Decimal("3500"), 100, Decimal("2800")),
    ("Bread", Decimal("1500"), 30, Decimal("1000")),
    ("Rice", Decimal("2500"), 80, Decimal("2000")),
    ("Water", Decimal("800"), 120, Decimal("500")),
]


async def seed() -> None:
    settings = get_settings()
    phone = normalize_phone(settings.allowed_phone_list[0] if settings.allowed_phone_list else "+255700000000")

    async with async_session_factory() as db:
        existing = await db.execute(select(Shop).limit(1))
        if existing.scalar_one_or_none():
            print("Shop already exists, skipping seed.")
            return

        async with transactional(db):
            shop = Shop(name="Demo Shop", currency="TZS")
            db.add(shop)
            await db.flush()

            owner = User(
                shop_id=shop.id,
                phone=phone,
                name="Shop Owner",
                role=UserRole.OWNER,
                password_hash=hash_password("changeme"),
            )
            db.add(owner)
            db.add(ShopPhoneNumber(shop_id=shop.id, phone=phone, label="owner"))
            db.add(Subscription(shop_id=shop.id, plan="trial", status="trialing"))

            for name, price, qty, cost in SAMPLE_PRODUCTS:
                db.add(
                    Product(
                        shop_id=shop.id,
                        name=name,
                        price=price,
                        cost_price=cost,
                        stock_qty=qty,
                        reorder_at=5,
                    )
                )

        print(f"Seeded shop '{shop.name}' (id={shop.id})")
        print(f"Owner phone: {phone}, password: changeme")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
