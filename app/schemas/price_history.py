import datetime

from .base import BaseSchema


class PriceHistoryRead(BaseSchema):
    id: int
    product_id: int
    price: float
    timestamp: datetime.datetime
