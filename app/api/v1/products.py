from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import PriceHistory, Product
from app.schemas import PriceHistoryRead


router = APIRouter(prefix="/products", tags=["products"])


@router.get(
    "/{product_id}/history",
    response_model=list[PriceHistoryRead],
    dependencies=[Depends(get_current_user)],
)
async def get_product_history(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PriceHistoryRead]:
    product_result = await db.execute(select(Product.id).where(Product.id == product_id))
    product_exists = product_result.scalar_one_or_none()

    if product_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.timestamp.asc())
    )
    history = result.scalars().all()
    return [PriceHistoryRead.model_validate(item) for item in history]
