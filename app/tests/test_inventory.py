import pytest

from app.engines.inventory import inventory_engine
from app.parser.command_parser import CommandParser


@pytest.mark.asyncio
async def test_stock_add(db_session):
    session, shop, user, product = db_session
    before = product.stock_qty
    intent = CommandParser().parse("stock add soda 5")
    msg = await inventory_engine.execute(
        session,
        shop_id=shop.id,
        user_id=user.id,
        role=user.role,
        intent=intent,
    )
    assert "Stock updated" in msg
    await session.refresh(product)
    assert product.stock_qty == before + 5


@pytest.mark.asyncio
async def test_stock_all(db_session):
    session, shop, user, product = db_session
    intent = CommandParser().parse("stock all")
    msg = await inventory_engine.execute(
        session,
        shop_id=shop.id,
        user_id=user.id,
        role=user.role,
        intent=intent,
    )
    assert "Soda" in msg
