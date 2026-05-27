from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transactional(session: AsyncSession):
    """Begin a transaction or nested savepoint if one is already active."""
    if session.in_transaction():
        async with session.begin_nested():
            yield
    else:
        async with session.begin():
            yield
