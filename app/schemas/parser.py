"""Pydantic schema for normalized parser output."""

import datetime

from .base import BaseSchema


class PriceUpdateSchema(BaseSchema):
    """Normalized product data returned by any parser implementation."""

    url: str
    title: str | None
    price: float | None
    parsed_at: datetime.datetime
