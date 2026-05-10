from app.schemas import PriceUpdateSchema

from .exceptions import ParserError
from .factory import get_parser_for_url


async def parse_product_url(url: str) -> PriceUpdateSchema:
    parser = get_parser_for_url(url)

    try:
        return await parser.parse(url)
    except ParserError:
        raise
    except Exception as exc:
        raise ParserError("Unexpected parser error") from exc
