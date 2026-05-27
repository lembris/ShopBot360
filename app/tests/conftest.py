import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
from app.database.models.product import Product
from app.database.models.shop import Shop
from app.database.models.user import User
from app.core.constants import UserRole
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        shop = Shop(name="Test Shop", currency="TZS")
        session.add(shop)
        await session.flush()
        user = User(
            shop_id=shop.id,
            phone="+255700000001",
            role=UserRole.OWNER,
        )
        session.add(user)
        product = Product(
            shop_id=shop.id,
            name="Soda",
            price=Decimal("1500"),
            stock_qty=10,
            cost_price=Decimal("1000"),
        )
        session.add(product)
        await session.commit()
        yield session, shop, user, product
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
