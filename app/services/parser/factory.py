from urllib.parse import urlparse

from .demo import DemoParser
from .exceptions import ParserNotSupportedError


def get_parser_for_url(url: str) -> DemoParser:
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ParserNotSupportedError("Invalid product URL")

    return DemoParser()
