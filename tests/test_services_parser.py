"""Unit tests for the parser layer (DemoParser, factory, service)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas import PriceUpdateSchema
from app.services.parser.base import BaseParser
from app.services.parser.demo import DemoParser
from app.services.parser.exceptions import ParserError, ParserNotSupportedError
from app.services.parser.factory import get_parser_for_url
from app.services.parser.service import parse_product_url


# ---------------------------------------------------------------------------
# DemoParser
# ---------------------------------------------------------------------------

async def test_demo_parser_returns_schema():
    """DemoParser must return a valid PriceUpdateSchema instance."""
    parser = DemoParser()
    result = await parser.parse("https://shop.example.com/item-1")
    assert isinstance(result, PriceUpdateSchema)
    assert result.url == "https://shop.example.com/item-1"
    assert result.price is not None
    assert result.parsed_at is not None


async def test_demo_parser_deterministic():
    """Same URL must always produce the same price."""
    parser = DemoParser()
    url = "https://shop.example.com/laptop-pro-15"
    result1 = await parser.parse(url)
    result2 = await parser.parse(url)
    assert result1.price == result2.price


async def test_demo_parser_price_in_range():
    """DemoParser price must always be in [10.0, 60.0]."""
    parser = DemoParser()
    for url in [
        "https://a.com/x",
        "https://very-long-domain-name.shop/category/subcategory/product-slug-123",
        "http://b.org/y?q=1&p=2",
    ]:
        result = await parser.parse(url)
        assert 10.0 <= result.price <= 60.0, f"Price {result.price} out of range for {url}"


async def test_demo_parser_title_derived_from_path():
    """DemoParser title must be derived from the URL path."""
    parser = DemoParser()
    result = await parser.parse("https://shop.example.com/red-running-shoes")
    assert "Red Running Shoes" in result.title


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_factory_invalid_url_raises():
    """Non-URL strings must raise ParserNotSupportedError."""
    with pytest.raises(ParserNotSupportedError):
        get_parser_for_url("not-a-url")


def test_factory_empty_string_raises():
    """Empty string must raise ParserNotSupportedError."""
    with pytest.raises(ParserNotSupportedError):
        get_parser_for_url("")


def test_factory_valid_url_returns_parser():
    """Valid URL must return a BaseParser subclass instance."""
    parser = get_parser_for_url("https://shop.example.com/item")
    assert isinstance(parser, BaseParser)
    assert isinstance(parser, DemoParser)


# ---------------------------------------------------------------------------
# Service (parse_product_url orchestration)
# ---------------------------------------------------------------------------

async def test_service_returns_schema_for_valid_url():
    """parse_product_url must return PriceUpdateSchema for a valid URL."""
    result = await parse_product_url("https://shop.example.com/test")
    assert isinstance(result, PriceUpdateSchema)


async def test_service_wraps_unknown_exception_in_parser_error():
    """Unexpected exceptions from parser.parse must be re-raised as ParserError."""
    with patch.object(DemoParser, "parse", new=AsyncMock(side_effect=RuntimeError("boom"))):
        with pytest.raises(ParserError):
            await parse_product_url("https://shop.example.com/test")


async def test_service_propagates_parser_error():
    """ParserError raised inside parser.parse must propagate unchanged."""
    with patch.object(DemoParser, "parse", new=AsyncMock(side_effect=ParserError("bad"))):
        with pytest.raises(ParserError, match="bad"):
            await parse_product_url("https://shop.example.com/test")
