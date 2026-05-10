from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import RefreshToken, UserLoginEmail, UserRegisterEmail, UserTelegramAuth
from app.core.security import create_tokens_for_user, get_password_hash, verify_password
from app.db.session import get_db
from app.models import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RefreshToken, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterEmail, db: AsyncSession = Depends(get_db)) -> RefreshToken:
    query = select(User).where(User.email == payload.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )

    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    return create_tokens_for_user(new_user.id)


@router.post("/login", response_model=RefreshToken)
async def login(payload: UserLoginEmail, db: AsyncSession = Depends(get_db)) -> RefreshToken:
    query = select(User).where(User.email == payload.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return create_tokens_for_user(user.id)


@router.post("/telegram", response_model=RefreshToken, status_code=status.HTTP_200_OK)
async def telegram_auth(
    payload: UserTelegramAuth,
    db: AsyncSession = Depends(get_db),
) -> RefreshToken:
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
        await db.commit()
        await db.refresh(user)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate telegram user",
        )

    return create_tokens_for_user(user.id)
