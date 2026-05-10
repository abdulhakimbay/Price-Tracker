import datetime

from pydantic import EmailStr

from .base import BaseSchema


class UserRegisterEmail(BaseSchema):
    email: EmailStr
    password: str


class UserLoginEmail(BaseSchema):
    email: EmailStr
    password: str


class UserTelegramAuth(BaseSchema):
    telegram_user_id: int
    telegram_username: str | None = None
    telegram_full_name: str | None = None


class Token(BaseSchema):
    access_token: str
    token_type: str


class RefreshToken(Token):
    refresh_token: str


class UserRead(BaseSchema):
    id: int
    email: EmailStr | None
    telegram_user_id: int | None
    telegram_username: str | None
    telegram_full_name: str | None
    is_active: bool
    created_at: datetime.datetime
