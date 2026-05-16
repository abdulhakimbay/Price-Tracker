"""Integration tests for authentication endpoints."""

from tests.conftest import auth_headers, make_user


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register
# ---------------------------------------------------------------------------

async def test_register_success(client):
    """Successful registration must return 201 with both tokens."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "secret123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client, db_session):
    """Registering with an already-used email must return 400."""
    await make_user(db_session, email="dup@example.com")
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "secret123"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------

async def test_login_success(client, db_session):
    """Valid credentials must return 200 with both tokens."""
    await make_user(db_session, email="login@example.com", password="pass123")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "pass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client, db_session):
    """Wrong password must return 401."""
    await make_user(db_session, email="wrongpass@example.com", password="correct")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_user(client):
    """Login for unknown email must return 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "pass"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/auth/telegram
# ---------------------------------------------------------------------------

async def test_telegram_auth_creates_user(client, db_session):
    """Telegram auth for a new user must return 200 and create the user."""
    response = await client.post(
        "/api/v1/auth/telegram",
        json={
            "telegram_user_id": 111222333,
            "telegram_username": "johndoe",
            "telegram_full_name": "John Doe",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_telegram_auth_updates_existing(client, db_session):
    """Telegram auth for an existing user must update the username."""
    await make_user(
        db_session,
        email=None,
        password=None,
        telegram_user_id=999888777,
        telegram_username="old_name",
    )
    response = await client.post(
        "/api/v1/auth/telegram",
        json={
            "telegram_user_id": 999888777,
            "telegram_username": "new_name",
            "telegram_full_name": "Updated Name",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
