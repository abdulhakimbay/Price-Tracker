from sqlalchemy import ForeignKey, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, intpk, created_at, updated_at


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    target_price: Mapped[float]
    is_notified: Mapped[bool] = mapped_column(server_default=text("false"))
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    user: Mapped["User"] = relationship(back_populates="subscriptions")
    product: Mapped["Product"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product"),
    )
