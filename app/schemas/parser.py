import datetime

from .base import BaseSchema


class PriceUpdateSchema(BaseSchema):
    url: str
    title: str | None
    price: float | None
    parsed_at: datetime.datetime
