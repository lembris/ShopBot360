import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"

    shop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(50))
    barcode: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    reorder_at: Mapped[int] = mapped_column(Integer, default=5)
    unit: Mapped[str] = mapped_column(String(20), default="pcs")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    shop = relationship("Shop", back_populates="products")
