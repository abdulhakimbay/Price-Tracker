from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, intpk, created_at


class User(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    created_at: Mapped[created_at]
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
