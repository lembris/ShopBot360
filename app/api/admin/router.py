import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CreditType
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import create_access_token, decode_access_token, hash_password, normalize_phone, verify_password
from app.database.connection import get_db
from app.database.transaction import transactional
from app.database.models.credit_ledger import CreditLedger
from app.database.models.product import Product
from app.database.models.sale import Sale, SaleItem
from app.database.models.shop import Shop
from app.database.models.user import User
from app.engines.debt import debt_engine
from app.engines.reports import report_engine
from app.parser.intents import Intent
from app.schemas.parser import IntentResult
from app.services.customers import customer_ledger, list_customers
from app.services.dashboard import build_dashboard
from app.services import audit
from app.services.sales import sale_items_summaries
from app.services.tenant import onboard_shop
from app.services.web_pos import checkout_cart

router = APIRouter(prefix="/admin", tags=["admin"])


class LoginRequest(BaseModel):
    phone: str
    password: str


class ProductCreate(BaseModel):
    name: str
    price: Decimal
    stock_qty: int = 0
    cost_price: Decimal | None = None
    reorder_at: int = 5
    unit: str = "pcs"
    category: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    price: Decimal | None = None
    stock_qty: int | None = None
    cost_price: Decimal | None = None
    reorder_at: int | None = None
    unit: str | None = None
    category: str | None = None


class SetPasswordRequest(BaseModel):
    password: str


class CustomerPaymentRequest(BaseModel):
    customer_name: str
    amount: Decimal
    note: str | None = None


class PosLineItem(BaseModel):
    product_id: uuid.UUID
    qty: int


class PosCheckoutRequest(BaseModel):
    items: list[PosLineItem]
    payment_method: str = "cash"
    customer_name: str | None = None


def _product_payload(product: Product) -> dict:
    return {
        "id": str(product.id),
        "name": product.name,
        "price": float(product.price),
        "cost_price": float(product.cost_price) if product.cost_price is not None else None,
        "stock_qty": product.stock_qty,
        "reorder_at": product.reorder_at,
        "unit": product.unit,
        "category": product.category,
    }


async def _get_product(
    product_id: uuid.UUID,
    shop_id: uuid.UUID,
    db: AsyncSession,
) -> Product:
    product = await db.get(Product, product_id)
    if not product or product.shop_id != shop_id or not product.is_active:
        raise HTTPException(404, "Product not found")
    return product


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
    phone = normalize_phone(body.phone)
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token(str(user.id), {"shop_id": str(user.shop_id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/dashboard")
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await db.get(Shop, user.shop_id)
    if not shop:
        raise HTTPException(404, "Shop not found")
    return await build_dashboard(db, shop)


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
    return [_product_payload(p) for p in products]


@router.get("/products/{product_id}")
async def get_product(
    product_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _get_product(product_id, user.shop_id, db)
    return _product_payload(product)


@router.post("/products")
async def create_product(
    body: ProductCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async with transactional(db):
        product = Product(
            shop_id=user.shop_id,
            name=body.name.strip(),
            price=body.price,
            stock_qty=body.stock_qty,
            cost_price=body.cost_price,
            reorder_at=body.reorder_at,
            unit=body.unit,
            category=body.category,
        )
        db.add(product)
        await db.flush()
    return _product_payload(product)


@router.put("/products/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async with transactional(db):
        product = await _get_product(product_id, user.shop_id, db)
        if body.name is not None:
            product.name = body.name.strip()
        if body.price is not None:
            product.price = body.price
        if body.stock_qty is not None:
            product.stock_qty = body.stock_qty
        if body.cost_price is not None:
            product.cost_price = body.cost_price
        if body.reorder_at is not None:
            product.reorder_at = body.reorder_at
        if body.unit is not None:
            product.unit = body.unit
        if body.category is not None:
            product.category = body.category
    return _product_payload(product)


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async with transactional(db):
        product = await _get_product(product_id, user.shop_id, db)
        product.is_active = False
    return {"status": "deleted", "id": str(product_id)}


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
    summaries = await sale_items_summaries(db, [s.id for s in sales])
    return [
        {
            "id": str(s.id),
            "receipt_no": s.receipt_no,
            "customer_name": s.customer_name,
            "product_names": summaries.get(s.id, ""),
            "total_amount": float(s.total_amount),
            "payment_method": s.payment_method,
            "is_credit": s.is_credit,
            "sold_at": s.sold_at.isoformat() if s.sold_at else None,
        }
        for s in sales
    ]


@router.get("/sales/{sale_id}")
async def get_sale(
    sale_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sale = await db.get(Sale, sale_id)
    if not sale or sale.shop_id != user.shop_id:
        raise HTTPException(404, "Sale not found")

    items_result = await db.execute(
        select(SaleItem, Product.name)
        .join(Product, Product.id == SaleItem.product_id)
        .where(SaleItem.sale_id == sale_id)
    )
    items = [
        {
            "product_id": str(item.product_id),
            "product_name": product_name,
            "qty": item.qty,
            "unit_price": float(item.unit_price),
            "total": float(item.total),
        }
        for item, product_name in items_result.all()
    ]

    return {
        "id": str(sale.id),
        "receipt_no": sale.receipt_no,
        "customer_name": sale.customer_name,
        "total_amount": float(sale.total_amount),
        "payment_method": sale.payment_method,
        "is_credit": sale.is_credit,
        "sold_at": sale.sold_at.isoformat() if sale.sold_at else None,
        "items": items,
    }


@router.get("/customers")
async def get_customers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_customers(db, user.shop_id)


@router.get("/customers/detail")
async def get_customer_detail(
    name: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await customer_ledger(db, user.shop_id, name.strip())


@router.post("/customers/payment")
async def record_customer_payment(
    body: CustomerPaymentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer_name = body.customer_name.strip()
    if not customer_name:
        raise HTTPException(400, "Customer name required")
    if body.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    async with transactional(db):
        db.add(
            CreditLedger(
                shop_id=user.shop_id,
                customer_name=customer_name,
                amount=body.amount,
                type=CreditType.PAYMENT,
                note=body.note,
                created_by=user.id,
            )
        )
        await audit.log_action(
            db,
            shop_id=user.shop_id,
            user_id=user.id,
            action="payment_recorded",
            entity_type="credit",
            metadata={"customer": customer_name, "amount": str(body.amount)},
        )

    balance = await debt_engine.customer_balance(db, user.shop_id, customer_name)
    return {
        "status": "ok",
        "customer_name": customer_name,
        "amount": float(body.amount),
        "balance": float(balance),
    }


@router.post("/pos/checkout")
async def pos_checkout(
    body: PosCheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await db.get(Shop, user.shop_id)
    currency = shop.currency if shop else "TZS"
    try:
        return await checkout_cart(
            db,
            shop_id=user.shop_id,
            user_id=user.id,
            role=user.role,
            items=[{"product_id": str(i.product_id), "qty": i.qty} for i in body.items],
            payment_method=body.payment_method,
            customer_name=body.customer_name,
            currency=currency,
        )
    except ValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


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
    body: SetPasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async with transactional(db):
        user.password_hash = hash_password(body.password)
    return {"status": "ok"}
