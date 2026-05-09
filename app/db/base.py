from sqlalchemy import func, text
from sqlalchemy.orm import DeclarativeBase
from typing import Annotated
from sqlalchemy.orm import mapped_column
import datetime


class Base(DeclarativeBase):
    pass


intpk = Annotated[int, mapped_column(primary_key=True)]

created_at = Annotated[datetime.datetime, mapped_column(
    default=lambda: datetime.datetime.now(datetime.UTC), 
    server_default=text("TIMEZONE('utc', now())"),
    nullable=False
)]

updated_at = Annotated[datetime.datetime, mapped_column(
    default=lambda: datetime.datetime.now(datetime.UTC),
    server_default=text("TIMEZONE('utc', now())"),
    onupdate=func.now(), 
    nullable=False
)]