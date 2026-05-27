import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin


class ShopPhoneNumber(UUIDPrimaryKeyMixin, Base):
    """Maps WhatsApp inbound numbers to shops (multi-tenant routing)."""

    __tablename__ = "shop_phone_numbers"
    __table_args__ = (UniqueConstraint("phone", name="uq_shop_phone"),)

    shop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str | None] = mapped_column(String(50))

    shop = relationship("Shop")
