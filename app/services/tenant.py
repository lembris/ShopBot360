import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import normalize_phone
from app.database.models.shop_phone import ShopPhoneNumber
from app.database.models.user import User


async def resolve_user_by_phone(db: AsyncSession, phone: str) -> User:
    normalized = normalize_phone(phone)
    result = await db.execute(
        select(User).where(User.phone == normalized, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("Phone not registered for any shop")
    return user


async def resolve_shop_by_inbound_phone(db: AsyncSession, phone: str) -> uuid.UUID | None:
    normalized = normalize_phone(phone)
    result = await db.execute(
        select(ShopPhoneNumber).where(ShopPhoneNumber.phone == normalized)
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        return mapping.shop_id
    user = await resolve_user_by_phone(db, phone)
    return user.shop_id


async def get_shop_users(db: AsyncSession, shop_id: uuid.UUID, role: str | None = None) -> list[User]:
    q = select(User).where(User.shop_id == shop_id, User.is_active.is_(True))
    if role:
        q = q.where(User.role == role)
    result = await db.execute(q)
    return list(result.scalars().all())


async def onboard_shop(
    db: AsyncSession,
    *,
    shop_name: str,
    owner_phone: str,
    owner_name: str | None = None,
    currency: str = "TZS",
) -> tuple[uuid.UUID, uuid.UUID]:
    from app.database.models.shop import Shop
    from app.core.constants import UserRole

    shop = Shop(name=shop_name, currency=currency)
    db.add(shop)
    await db.flush()

    user = User(
        shop_id=shop.id,
        phone=normalize_phone(owner_phone),
        name=owner_name or "Owner",
        role=UserRole.OWNER,
    )
    db.add(user)
    db.add(ShopPhoneNumber(shop_id=shop.id, phone=normalize_phone(owner_phone), label="owner"))
    await db.flush()
    return shop.id, user.id
