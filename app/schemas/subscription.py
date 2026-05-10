import datetime

from .base import BaseSchema
from .product import ProductRead


class SubscriptionCreate(BaseSchema):
    url: str
    target_price: float


class SubscriptionUpdate(BaseSchema):
    target_price: float


class SubscriptionRead(BaseSchema):
    id: int
    user_id: int
    product_id: int
    target_price: float
    is_notified: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    product: ProductRead
