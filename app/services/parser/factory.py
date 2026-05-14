"""Parser factory helpers."""

import logging
from urllib.parse import urlparse

from .base import BaseParser
from .demo import DemoParser
from .exceptions import ParserNotSupportedError


logger = logging.getLogger(__name__)


def get_parser_for_url(url: str) -> BaseParser:
    """Return the parser implementation that can handle the provided URL."""
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logger.warning("event=parser_selection_failed reason=invalid_url url=%s", url)
        raise ParserNotSupportedError("Invalid product URL")

    logger.info("event=parser_selected parser=demo url=%s", url)
    return DemoParser()
