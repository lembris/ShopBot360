#!/usr/bin/env python3
"""Simulate exact user chat sequence."""
import asyncio
import sys
import uuid

sys.path.insert(0, "/app")

from app.database.connection import async_session_factory
from app.services.message_handler import message_handler
from app.services.session import session_service

PHONE = "+255746082561"
SHOP_ID = None


async def get_shop_id(db):
    from app.services.tenant import resolve_user_by_phone
    user = await resolve_user_by_phone(db, PHONE)
    return str(user.shop_id)


async def run_sequence(label: str, commands: list[str]) -> None:
    global SHOP_ID
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    async with async_session_factory() as db:
        shop_id = await get_shop_id(db)
    await session_service.clear(shop_id, PHONE)

    for i, cmd in enumerate(commands, 1):
        async with async_session_factory() as db:
            session = await session_service.get(shop_id, PHONE)
            try:
                reply = await message_handler.handle_inbound(
                    db,
                    from_phone=PHONE,
                    text=cmd,
                    message_id=f"seq-{uuid.uuid4().hex[:8]}",
                )
                status = "OK"
            except Exception as exc:
                reply = f"EXCEPTION: {exc}"
                status = type(exc).__name__
        sess = await session_service.get(shop_id, PHONE)
        print(f"\n[{status}] User: {cmd!r}")
        print(f"Bot:  {reply or '(empty)'}")
        if sess:
            print(f"Session: {sess}")


async def main() -> None:
    await run_sequence("User chat replay", [
        "help",
        "report",
        "report today",
        "uza soda mbili",
        "2",
        "report today",
        "stock all",
        "stock add",
    ])

    await run_sequence("Correct sell flow", [
        "sell 2 soda 1500",
        "report today",
        "stock all",
    ])


if __name__ == "__main__":
    asyncio.run(main())
