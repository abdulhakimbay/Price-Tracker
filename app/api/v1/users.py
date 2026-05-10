import datetime

from fastapi import APIRouter

from app.schemas import UserRead


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user() -> UserRead:
    return UserRead(
        id=0,
        email="demo@example.com",
        telegram_user_id=123456789,
        telegram_username="demo_user",
        telegram_full_name="Demo User",
        is_active=True,
        created_at=datetime.datetime.now(datetime.UTC),
    )
