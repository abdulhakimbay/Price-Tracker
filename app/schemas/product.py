import datetime

from .base import BaseSchema


class ProductRead(BaseSchema):
    id: int
    url: str
    title: str | None
    current_price: float | None
    last_parsed_at: datetime.datetime | None
