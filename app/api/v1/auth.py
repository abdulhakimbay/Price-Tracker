"""Authentication endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import RefreshToken, UserLoginEmail, UserRegisterEmail, UserTelegramAuth
from app.core.security import create_tokens_for_user, get_password_hash, verify_password
from app.db.session import get_db
from app.models import User


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Load a user by email for registration and login flows."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _save_changes(db: AsyncSession) -> None:
    """Commit the current transaction and rollback if persistence fails."""
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise


@router.post("/register", response_model=RefreshToken, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterEmail, db: AsyncSession = Depends(get_db)) -> RefreshToken:
    """Register a new email-based user and return an auth token pair."""
    logger.info("event=register_requested email=%s", payload.email)
    existing_user = await _get_user_by_email(db, payload.email)
    if existing_user:
        logger.warning("event=register_rejected reason=email_exists email=%s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(new_user)

    try:
        await _save_changes(db)
        await db.refresh(new_user)
    except SQLAlchemyError:
        logger.exception("event=register_failed email=%s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    logger.info("event=register_succeeded user_id=%s email=%s", new_user.id, new_user.email)
    return create_tokens_for_user(new_user.id)


@router.post("/login", response_model=RefreshToken)
async def login(payload: UserLoginEmail, db: AsyncSession = Depends(get_db)) -> RefreshToken:
    """Authenticate an email-based user and return an auth token pair."""
    logger.info("event=login_requested email=%s", payload.email)
    user = await _get_user_by_email(db, payload.email)

    if user is None or user.hashed_password is None:
        logger.warning("event=login_rejected reason=invalid_credentials email=%s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        logger.warning("event=login_rejected reason=invalid_credentials email=%s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    logger.info("event=login_succeeded user_id=%s email=%s", user.id, user.email)
    return create_tokens_for_user(user.id)


@router.post("/telegram", response_model=RefreshToken, status_code=status.HTTP_200_OK)
async def telegram_auth(
    payload: UserTelegramAuth,
    db: AsyncSession = Depends(get_db),
) -> RefreshToken:
    """Create or update a Telegram-based user and return an auth token pair."""
    logger.info("event=telegram_auth_requested telegram_user_id=%s", payload.telegram_user_id)
    query = select(User).where(User.telegram_user_id == payload.telegram_user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_user_id=payload.telegram_user_id,
            telegram_username=payload.telegram_username,
            telegram_full_name=payload.telegram_full_name,
        )
        db.add(user)
    else:
        user.telegram_username = payload.telegram_username
        user.telegram_full_name = payload.telegram_full_name

    try:
        await _save_changes(db)
        await db.refresh(user)
    except SQLAlchemyError:
        logger.exception(
            "event=telegram_auth_failed telegram_user_id=%s",
            payload.telegram_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate telegram user",
        )

    logger.info("event=telegram_auth_succeeded user_id=%s", user.id)
    return create_tokens_for_user(user.id)
