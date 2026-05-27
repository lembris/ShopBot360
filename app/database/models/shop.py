from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_CURRENCY, DEFAULT_TIMEZONE
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Shop(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shops"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default=DEFAULT_CURRENCY)
    timezone: Mapped[str] = mapped_column(String(50), default=DEFAULT_TIMEZONE)

    users = relationship("User", back_populates="shop")
    products = relationship("Product", back_populates="shop")
    subscriptions = relationship("Subscription", back_populates="shop")
