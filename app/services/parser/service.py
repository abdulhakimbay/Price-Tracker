"""Parser orchestration services."""

import logging

from app.schemas import PriceUpdateSchema

from .exceptions import ParserError
from .factory import get_parser_for_url


logger = logging.getLogger(__name__)


async def parse_product_url(url: str) -> PriceUpdateSchema:
    """Resolve a parser for the URL and normalize any unexpected errors."""
    parser = get_parser_for_url(url)

    try:
        return await parser.parse(url)
    except ParserError:
        logger.exception("event=parser_failed_known url=%s", url)
        raise
    except Exception as exc:
        logger.exception("event=parser_failed_unknown url=%s", url)
        raise ParserError("Unexpected parser error") from exc
