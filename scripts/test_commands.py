#!/usr/bin/env python3
"""Run commands through message_handler and print bot replies."""
import asyncio
import sys
import uuid

sys.path.insert(0, "/app")

from app.database.connection import async_session_factory
from app.services.message_handler import message_handler


PHONE = "+255746082561"

COMMANDS = [
    "help",
    "report",
    "report today",
    "stock all",
    "stock add",
    "stock add sugar 50",
    "sell 2 soda 1500",
    "report today",
    "profit today",
    "debt john",
    "paid john 5000",
    "credit report",
    "top products",
    "report week",
    "uza soda mbili",
    "2",
    "1500",
    "restock water 10",
    "price soda 1600",
    "new juice 2000 20",
]


async def main() -> None:
    for i, cmd in enumerate(COMMANDS, 1):
        async with async_session_factory() as db:
            try:
                reply = await message_handler.handle_inbound(
                    db,
                    from_phone=PHONE,
                    text=cmd,
                    message_id=f"test-{i}-{uuid.uuid4().hex[:8]}",
                )
                status = "OK"
            except Exception as exc:
                reply = str(exc)
                status = type(exc).__name__
        print(f"\n[{status}] > {cmd!r}")
        print(reply or "(empty reply)")


if __name__ == "__main__":
    asyncio.run(main())
