"""Pydantic schemas for product read responses."""

import datetime

from .base import BaseSchema


class ProductRead(BaseSchema):
    """Public representation of a tracked product returned by the API."""

    id: int
    url: str
    title: str | None
    current_price: float | None
    last_parsed_at: datetime.datetime | None
