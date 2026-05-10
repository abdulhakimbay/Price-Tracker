from abc import ABC, abstractmethod

from app.schemas import PriceUpdateSchema


class BaseParser(ABC):
    @abstractmethod
    async def parse(self, url: str) -> PriceUpdateSchema:
        raise NotImplementedError
