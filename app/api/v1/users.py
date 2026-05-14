"""User-related endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models import User
from app.schemas import UserRead


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    """Return the authenticated user's profile."""
    logger.info("event=current_user_requested user_id=%s", current_user.id)
    return UserRead.model_validate(current_user)
