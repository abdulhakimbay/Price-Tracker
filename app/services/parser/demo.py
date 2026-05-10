from datetime import datetime
from urllib.parse import urlparse

from app.schemas import PriceUpdateSchema

from .base import BaseParser


class DemoParser(BaseParser):
    async def parse(self, url: str) -> PriceUpdateSchema:
        parsed_url = urlparse(url)
        path = parsed_url.path.strip("/") or "product"
        title = path.replace("-", " ").replace("_", " ").title()

        # Deterministic fake price so the same URL produces the same demo result.
        price_seed = sum(ord(char) for char in url) % 5000
        price = round(10 + (price_seed / 100), 2)

        return PriceUpdateSchema(
            url=url,
            title=f"Demo {title}",
            price=price,
            parsed_at=datetime.utcnow(),
        )
