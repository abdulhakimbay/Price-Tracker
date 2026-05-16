"""Pydantic schema for price history read responses."""

import datetime

from .base import BaseSchema


class PriceHistoryRead(BaseSchema):
    """One historical price record for a tracked product."""

    id: int
    product_id: int
    price: float
    timestamp: datetime.datetime
