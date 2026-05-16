"""Authentication and token helpers."""

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas import RefreshToken


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against the stored hash."""
    logger.debug("event=password_verification_requested")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain-text password before it is persisted."""
    logger.debug("event=password_hash_requested")
    return pwd_context.hash(password)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_data: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token for the given subject."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra_data:
        to_encode.update(extra_data)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_data: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT refresh token for the given subject."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    if extra_data:
        to_encode.update(extra_data)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_tokens_for_user(user_id: int) -> RefreshToken:
    """Build the access and refresh token pair returned to clients."""
    logger.info("event=token_pair_created user_id=%s", user_id)
    return RefreshToken(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        token_type="bearer",
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT token."""
    logger.debug("event=token_decode_requested")
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
