"""SQLAlchemy models for products and price history."""

import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, intpk


class Product(Base):
    """Represent a tracked product URL with its latest price metadata."""

    __tablename__ = "products"

    id: Mapped[intpk]
    url: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str | None]
    current_price: Mapped[float | None]
    last_parsed_at: Mapped[datetime.datetime | None]
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="product")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="product")


class PriceHistory(Base):
    """Record one observed price for a product at a specific point in time."""

    __tablename__ = "price_history"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    price: Mapped[float]
    timestamp: Mapped[datetime.datetime] = mapped_column(index=True)
    product: Mapped["Product"] = relationship(back_populates="price_history")
