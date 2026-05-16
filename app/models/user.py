from sqlalchemy import CheckConstraint, text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, intpk, created_at


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "telegram_user_id IS NOT NULL OR (email IS NOT NULL AND hashed_password IS NOT NULL)",
            name="ck_users_has_auth_method",
        ),
    )

    id: Mapped[intpk]
    email: Mapped[str | None] = mapped_column(unique=True, index=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(nullable=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(nullable=True)
    telegram_full_name: Mapped[str | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    created_at: Mapped[created_at]
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
