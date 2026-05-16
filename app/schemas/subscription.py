"""Pydantic schemas for subscription create, update, and read operations."""

import datetime

from .base import BaseSchema
from .product import ProductRead


class SubscriptionCreate(BaseSchema):
    """Payload for creating a new subscription to a product URL."""

    url: str
    target_price: float


class SubscriptionUpdate(BaseSchema):
    """Payload for updating the target price of an existing subscription."""

    target_price: float


class SubscriptionRead(BaseSchema):
    """Public representation of a subscription returned by the API."""

    id: int
    user_id: int
    product_id: int
    target_price: float
    is_notified: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    product: ProductRead
