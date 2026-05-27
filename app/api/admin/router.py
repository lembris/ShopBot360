import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.database.connection import get_db
from app.database.transaction import transactional
from app.database.models.product import Product
from app.database.models.sale import Sale
from app.database.models.shop import Shop
from app.database.models.user import User
from app.engines.reports import report_engine
from app.parser.intents import Intent
from app.schemas.parser import IntentResult
from app.services.tenant import onboard_shop

router = APIRouter(prefix="/admin", tags=["admin"])


class LoginRequest(BaseModel):
    phone: str
    password: str


class ProductCreate(BaseModel):
    name: str
    price: Decimal
    stock_qty: int = 0
    cost_price: Decimal | None = None


class ShopOnboardRequest(BaseModel):
    shop_name: str
    owner_phone: str
    owner_name: str | None = None
    currency: str = "TZS"


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid user")
    return user


@router.post("/auth/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token(str(user.id), {"shop_id": str(user.shop_id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/shops/onboard")
async def onboard(body: ShopOnboardRequest, db: AsyncSession = Depends(get_db)):
    async with transactional(db):
        shop_id, user_id = await onboard_shop(
            db,
            shop_name=body.shop_name,
            owner_phone=body.owner_phone,
            owner_name=body.owner_name,
            currency=body.currency,
        )
    return {"shop_id": str(shop_id), "user_id": str(user_id)}


@router.get("/products")
async def list_products(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.shop_id == user.shop_id, Product.is_active.is_(True))
    )
    products = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "price": float(p.price),
            "stock_qty": p.stock_qty,
            "reorder_at": p.reorder_at,
        }
        for p in products
    ]


@router.post("/products")
async def create_product(
    body: ProductCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async with transactional(db):
        product = Product(
            shop_id=user.shop_id,
            name=body.name,
            price=body.price,
            stock_qty=body.stock_qty,
            cost_price=body.cost_price,
        )
        db.add(product)
        await db.flush()
    return {"id": str(product.id), "name": product.name}


@router.get("/sales")
async def list_sales(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(Sale)
        .where(Sale.shop_id == user.shop_id)
        .order_by(Sale.sold_at.desc())
        .limit(limit)
    )
    sales = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "receipt_no": s.receipt_no,
            "customer_name": s.customer_name,
            "total_amount": float(s.total_amount),
            "sold_at": s.sold_at.isoformat() if s.sold_at else None,
        }
        for s in sales
    ]


@router.get("/reports")
async def get_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await db.get(Shop, user.shop_id)
    today = await report_engine.execute(
        db,
        shop_id=user.shop_id,
        role=user.role,
        intent=IntentResult(intent=Intent.REPORT_TODAY),
        timezone=shop.timezone if shop else "Africa/Dar_es_Salaam",
        currency=shop.currency if shop else "TZS",
    )
    week = await report_engine.execute(
        db,
        shop_id=user.shop_id,
        role=user.role,
        intent=IntentResult(intent=Intent.REPORT_WEEK),
        timezone=shop.timezone if shop else "Africa/Dar_es_Salaam",
        currency=shop.currency if shop else "TZS",
    )
    return {"today": today, "week": week}


@router.post("/users/set-password")
async def set_password(
    password: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async with transactional(db):
        user.password_hash = hash_password(password)
    return {"status": "ok"}
