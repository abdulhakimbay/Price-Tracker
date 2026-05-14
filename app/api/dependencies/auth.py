"""Authentication-related FastAPI dependencies."""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import JWTError, decode_token
from app.db.session import get_db
from app.models import User


logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Resolve the authenticated user from the bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("event=auth_credentials_invalid reason=missing_subject")
            raise credentials_exception
        resolved_user_id = int(user_id)
    except (JWTError, ValueError):
        logger.warning("event=auth_credentials_invalid reason=token_decode_failed")
        raise credentials_exception

    query = select(User).where(User.id == resolved_user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning("event=auth_credentials_invalid reason=user_not_found user_id=%s", resolved_user_id)
        raise credentials_exception

    logger.info("event=auth_user_resolved user_id=%s", user.id)
    return user
