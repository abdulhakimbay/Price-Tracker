"""Subscription endpoints for the authenticated user."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import Product, Subscription, User
from app.schemas import SubscriptionCreate, SubscriptionRead, SubscriptionUpdate
from app.services.parser import parse_product_url
from app.services.parser.exceptions import ParserError


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


async def _get_or_create_product(db: AsyncSession, url: str) -> Product:
    """Load a product by URL or create one using the parser output."""
    product_result = await db.execute(select(Product).where(Product.url == url))
    product = product_result.scalar_one_or_none()
    if product is not None:
        logger.info("event=subscription_product_reused product_id=%s url=%s", product.id, url)
        return product

    parsed_product = None
    try:
        parsed_product = await parse_product_url(url)
    except ParserError:
        logger.exception("event=subscription_product_parse_failed url=%s", url)

    product = Product(
        url=url,
        title=parsed_product.title if parsed_product else None,
        current_price=parsed_product.price if parsed_product else None,
        last_parsed_at=parsed_product.parsed_at if parsed_product else None,
    )
    db.add(product)
    await db.flush()
    logger.info("event=subscription_product_created product_id=%s url=%s", product.id, url)
    return product


async def _get_owned_subscription_or_404(
    db: AsyncSession,
    *,
    subscription_id: int,
    user_id: int,
) -> Subscription:
    """Load a subscription owned by the current user or raise 404."""
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.product))
        .where(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id,
        )
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        logger.warning(
            "event=subscription_not_found subscription_id=%s user_id=%s",
            subscription_id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return subscription


@router.post(
    "/",
    response_model=SubscriptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    payload: SubscriptionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SubscriptionRead:
    """Create a subscription and attach it to a tracked product."""
    logger.info(
        "event=subscription_create_requested user_id=%s url=%s",
        current_user.id,
        payload.url,
    )
    product = await _get_or_create_product(db, payload.url)
    subscription = Subscription(
        user_id=current_user.id,
        product_id=product.id,
        target_price=payload.target_price,
    )
    db.add(subscription)

    try:
        await db.commit()
        await db.refresh(subscription, ["product"])
    except IntegrityError:
        await db.rollback()
        logger.warning(
            "event=subscription_create_rejected reason=duplicate user_id=%s product_id=%s",
            current_user.id,
            product.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription for this product already exists",
        )

    logger.info(
        "event=subscription_created subscription_id=%s user_id=%s",
        subscription.id,
        current_user.id,
    )
    return SubscriptionRead.model_validate(subscription)


@router.get("/", response_model=list[SubscriptionRead])
async def list_subscriptions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SubscriptionRead]:
    """Return all subscriptions owned by the authenticated user."""
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.product))
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    subscriptions = result.scalars().all()
    logger.info(
        "event=subscription_list_loaded user_id=%s count=%s",
        current_user.id,
        len(subscriptions),
    )
    return [SubscriptionRead.model_validate(subscription) for subscription in subscriptions]


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: int,
    payload: SubscriptionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SubscriptionRead:
    """Update the target price of an owned subscription."""
    subscription = await _get_owned_subscription_or_404(
        db,
        subscription_id=subscription_id,
        user_id=current_user.id,
    )
    subscription.target_price = payload.target_price
    await db.commit()
    await db.refresh(subscription, attribute_names=["product"])

    logger.info(
        "event=subscription_updated subscription_id=%s target_price=%s",
        subscription.id,
        subscription.target_price,
    )
    return SubscriptionRead.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Delete an owned subscription."""
    subscription = await _get_owned_subscription_or_404(
        db,
        subscription_id=subscription_id,
        user_id=current_user.id,
    )

    await db.delete(subscription)
    await db.commit()
    logger.info(
        "event=subscription_deleted subscription_id=%s user_id=%s",
        subscription_id,
        current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
