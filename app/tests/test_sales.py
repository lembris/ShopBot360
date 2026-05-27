import pytest
from unittest.mock import AsyncMock, patch

from app.engines.pos import pos_engine
from app.parser.command_parser import CommandParser
from app.core.exceptions import InsufficientStockError


@pytest.mark.asyncio
async def test_sale_reduces_stock(db_session):
    session, shop, user, product = db_session
    intent = CommandParser().parse("sell 2 soda 1500")

    with patch("app.engines.pos.cache_service.acquire_lock", new_callable=AsyncMock, return_value=True):
        with patch("app.engines.pos.cache_service.release_lock", new_callable=AsyncMock):
            msg = await pos_engine.execute(
                session,
                shop_id=shop.id,
                user_id=user.id,
                role=user.role,
                intent=intent,
            )

    assert "RECEIPT" in msg
    await session.refresh(product)
    assert product.stock_qty == 8


@pytest.mark.asyncio
async def test_insufficient_stock(db_session):
    session, shop, user, product = db_session
    product.stock_qty = 1
    await session.commit()
    intent = CommandParser().parse("sell 5 soda 1500")

    with patch("app.engines.pos.cache_service.acquire_lock", new_callable=AsyncMock, return_value=True):
        with patch("app.engines.pos.cache_service.release_lock", new_callable=AsyncMock):
            with pytest.raises(InsufficientStockError):
                await pos_engine.execute(
                    session,
                    shop_id=shop.id,
                    user_id=user.id,
                    role=user.role,
                    intent=intent,
                )
