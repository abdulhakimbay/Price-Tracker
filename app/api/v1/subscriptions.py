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


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


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
    product_result = await db.execute(select(Product).where(Product.url == payload.url))
    product = product_result.scalar_one_or_none()

    if product is None:
        parsed_product = None
        try:
            parsed_product = await parse_product_url(payload.url)
        except ParserError:
            parsed_product = None

        product = Product(
            url=payload.url,
            title=parsed_product.title if parsed_product else None,
            current_price=parsed_product.price if parsed_product else None,
            last_parsed_at=parsed_product.parsed_at if parsed_product else None,
        )
        db.add(product)
        await db.flush()

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription for this product already exists",
        )

    return SubscriptionRead.model_validate(subscription)


@router.get("/", response_model=list[SubscriptionRead])
async def list_subscriptions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SubscriptionRead]:
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.product))
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    subscriptions = result.scalars().all()
    return [SubscriptionRead.model_validate(subscription) for subscription in subscriptions]


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: int,
    payload: SubscriptionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SubscriptionRead:
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.product))
        .where(
            Subscription.id == subscription_id,
            Subscription.user_id == current_user.id,
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    subscription.target_price = payload.target_price
    await db.commit()
    await db.refresh(subscription, attribute_names=["product"])

    return SubscriptionRead.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == current_user.id,
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    await db.delete(subscription)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
