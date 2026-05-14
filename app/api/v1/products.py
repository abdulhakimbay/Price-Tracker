"""Product-related endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import PriceHistory, Product
from app.schemas import PriceHistoryRead, ProductRead


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


async def _get_product_or_404(db: AsyncSession, product_id: int) -> Product:
    """Load a product or raise a 404 response if it does not exist."""
    product_result = await db.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalar_one_or_none()
    if product is None:
        logger.warning("event=product_not_found product_id=%s", product_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.get(
    "/{product_id}",
    response_model=ProductRead,
)
async def get_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductRead:
    """Return the current state of a single tracked product."""
    logger.info("event=product_requested product_id=%s", product_id)
    product = await _get_product_or_404(db, product_id)
    return ProductRead.model_validate(product)


@router.get(
    "/{product_id}/history",
    response_model=list[PriceHistoryRead],
    dependencies=[Depends(get_current_user)],
)
async def get_product_history(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PriceHistoryRead]:
    """Return the ordered price history used by client-side charts."""
    logger.info("event=product_history_requested product_id=%s", product_id)
    await _get_product_or_404(db, product_id)

    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.timestamp.asc())
    )
    history = result.scalars().all()
    logger.info(
        "event=product_history_loaded product_id=%s records=%s",
        product_id,
        len(history),
    )
    return [PriceHistoryRead.model_validate(item) for item in history]
