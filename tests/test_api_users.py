"""Integration tests for the /users/me endpoint."""

from tests.conftest import auth_headers, make_user


async def test_get_me_authenticated(client, db_session):
    """Authenticated user must receive their own profile."""
    user = await make_user(db_session, email="me@example.com")
    response = await client.get("/api/v1/users/me", headers=auth_headers(user.id))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == "me@example.com"


async def test_get_me_unauthenticated(client):
    """Request without a token must return 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
