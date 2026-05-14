"""Parser abstractions."""

from abc import ABC, abstractmethod

from app.schemas import PriceUpdateSchema


class BaseParser(ABC):
    """Define the contract implemented by every concrete parser."""

    @abstractmethod
    async def parse(self, url: str) -> PriceUpdateSchema:
        """Return normalized price data for a product URL."""
        raise NotImplementedError
