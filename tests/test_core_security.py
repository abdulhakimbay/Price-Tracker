"""Unit tests for core security helpers (passwords and JWT tokens)."""

from datetime import timedelta

import pytest

from app.core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    create_tokens_for_user,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    """Hash a password and verify the round-trip is correct."""
    hashed = get_password_hash("my-secret")
    assert verify_password("my-secret", hashed) is True


def test_verify_wrong_password():
    """Wrong password must return False, not raise."""
    hashed = get_password_hash("correct")
    assert verify_password("wrong", hashed) is False


def test_create_access_token_decode():
    """Access token payload must contain the correct subject."""
    token = create_access_token(subject=42)
    payload = decode_token(token)
    assert payload["sub"] == "42"


def test_create_refresh_token_has_type():
    """Refresh token payload must carry type='refresh'."""
    token = create_refresh_token(subject=7)
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == "7"


def test_create_tokens_for_user():
    """create_tokens_for_user must return both tokens with correct type."""
    result = create_tokens_for_user(user_id=1)
    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"


def test_decode_invalid_token_raises():
    """Garbage string must raise JWTError."""
    with pytest.raises(JWTError):
        decode_token("this.is.garbage")


def test_access_token_expiry():
    """Already-expired token must raise JWTError on decode."""
    token = create_access_token(subject=1, expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_token(token)
