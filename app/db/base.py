"""SQLAlchemy declarative base and shared column type annotations."""

import datetime
from typing import Annotated

from sqlalchemy import func, text
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


# Reusable primary-key annotation.
intpk = Annotated[int, mapped_column(primary_key=True)]

# Reusable timestamp annotations that default to the current UTC time.
created_at = Annotated[datetime.datetime, mapped_column(
    default=lambda: datetime.datetime.now(datetime.UTC),
    server_default=text("TIMEZONE('utc', now())"),
    nullable=False,
)]

updated_at = Annotated[datetime.datetime, mapped_column(
    default=lambda: datetime.datetime.now(datetime.UTC),
    server_default=text("TIMEZONE('utc', now())"),
    onupdate=func.now(),
    nullable=False,
)]
