"""Pydantic schemas for user registration, login, and authentication tokens."""

import datetime

from pydantic import EmailStr

from .base import BaseSchema


class UserRegisterEmail(BaseSchema):
    """Payload for creating a new user account with email and password."""

    email: EmailStr
    password: str


class UserLoginEmail(BaseSchema):
    """Payload for authenticating an existing user with email and password."""

    email: EmailStr
    password: str


class UserTelegramAuth(BaseSchema):
    """Payload for authenticating or registering a Telegram user."""

    telegram_user_id: int
    telegram_username: str | None = None
    telegram_full_name: str | None = None


class Token(BaseSchema):
    """Response schema containing a single access token."""

    access_token: str
    token_type: str


class RefreshToken(Token):
    """Response schema containing both access and refresh tokens."""

    refresh_token: str


class UserRead(BaseSchema):
    """Public representation of a user returned by the API."""

    id: int
    email: EmailStr | None
    telegram_user_id: int | None
    telegram_username: str | None
    telegram_full_name: str | None
    is_active: bool
    created_at: datetime.datetime
