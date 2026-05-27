"""Stripe subscription billing (Phase 3)."""

import logging
import uuid

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.connection import get_db
from app.database.models.subscription import Subscription

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


def _stripe():
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(503, "Stripe not configured")
    stripe.api_key = settings.stripe_secret_key
    return stripe


@router.post("/checkout")
async def create_checkout(shop_id: str, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    s = _stripe()
    result = await db.execute(
        select(Subscription).where(Subscription.shop_id == uuid.UUID(shop_id))
    )
    sub = result.scalar_one_or_none()
    session = s.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id_basic, "quantity": 1}],
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        metadata={"shop_id": shop_id},
        customer=sub.stripe_customer_id if sub else None,
    )
    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

    if event["type"] == "customer.subscription.updated":
        data = event["data"]["object"]
        shop_id = data.get("metadata", {}).get("shop_id")
        if shop_id:
            async with db.begin():
                result = await db.execute(
                    select(Subscription).where(Subscription.shop_id == uuid.UUID(shop_id))
                )
                sub = result.scalar_one_or_none()
                if sub:
                    sub.status = data.get("status", sub.status)
                    sub.stripe_subscription_id = data.get("id")

    return {"received": True}


PLAN_FEATURES = {
    "trial": {"max_products": 50, "analytics": False, "ai_parsing": False},
    "basic": {"max_products": 500, "analytics": True, "ai_parsing": True},
    "pro": {"max_products": 5000, "analytics": True, "ai_parsing": True},
}


def check_feature(plan: str, feature: str) -> bool:
    return PLAN_FEATURES.get(plan, PLAN_FEATURES["trial"]).get(feature, False)
