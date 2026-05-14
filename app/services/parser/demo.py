"""Demo parser implementation used before real website integrations exist."""

from datetime import datetime
import logging
from urllib.parse import urlparse

from app.schemas import PriceUpdateSchema

from .base import BaseParser


logger = logging.getLogger(__name__)


class DemoParser(BaseParser):
    """Produce deterministic fake product data from the URL itself."""

    async def parse(self, url: str) -> PriceUpdateSchema:
        """Generate repeatable demo data so the rest of the app can be exercised."""
        logger.info("event=parser_demo_started url=%s", url)
        parsed_url = urlparse(url)
        path = parsed_url.path.strip("/") or "product"
        title = path.replace("-", " ").replace("_", " ").title()

        # Deterministic fake price so the same URL produces the same demo result.
        price_seed = sum(ord(char) for char in url) % 5000
        price = round(10 + (price_seed / 100), 2)

        logger.info("event=parser_demo_succeeded url=%s price=%s", url, price)
        return PriceUpdateSchema(
            url=url,
            title=f"Demo {title}",
            price=price,
            parsed_at=datetime.utcnow(),
        )
