"""Integration tests for the /subscriptions endpoints."""

from tests.conftest import auth_headers, make_user

PRODUCT_URL = "https://shop.example.com/red-sneakers"


# ---------------------------------------------------------------------------
# POST /api/v1/subscriptions/
# ---------------------------------------------------------------------------

async def test_create_subscription_unauthenticated(client):
    """Creating a subscription without auth must return 401."""
    response = await client.post(
        "/api/v1/subscriptions/",
        json={"url": PRODUCT_URL, "target_price": 50.0},
    )
    assert response.status_code == 401


async def test_create_subscription_success(client, db_session):
    """Authenticated user must be able to create a subscription."""
    user = await make_user(db_session, email="sub@example.com")
    response = await client.post(
        "/api/v1/subscriptions/",
        json={"url": PRODUCT_URL, "target_price": 50.0},
        headers=auth_headers(user.id),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["target_price"] == 50.0
    assert data["user_id"] == user.id
    assert data["product"]["url"] == PRODUCT_URL


async def test_create_subscription_duplicate(client, db_session):
    """Duplicate subscription for the same URL must return 400."""
    user = await make_user(db_session, email="dup_sub@example.com")
    headers = auth_headers(user.id)
    payload = {"url": PRODUCT_URL, "target_price": 50.0}

    r1 = await client.post("/api/v1/subscriptions/", json=payload, headers=headers)
    assert r1.status_code == 201

    r2 = await client.post("/api/v1/subscriptions/", json=payload, headers=headers)
    assert r2.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/subscriptions/
# ---------------------------------------------------------------------------

async def test_list_subscriptions_empty(client, db_session):
    """New user with no subscriptions must receive an empty list."""
    user = await make_user(db_session, email="empty@example.com")
    response = await client.get("/api/v1/subscriptions/", headers=auth_headers(user.id))
    assert response.status_code == 200
    assert response.json() == []


async def test_list_subscriptions_populated(client, db_session):
    """User must only see their own subscriptions."""
    user_a = await make_user(db_session, email="usera@example.com")
    user_b = await make_user(db_session, email="userb@example.com")

    await client.post(
        "/api/v1/subscriptions/",
        json={"url": "https://shop.example.com/item-a", "target_price": 10.0},
        headers=auth_headers(user_a.id),
    )
    await client.post(
        "/api/v1/subscriptions/",
        json={"url": "https://shop.example.com/item-b", "target_price": 20.0},
        headers=auth_headers(user_b.id),
    )

    response = await client.get("/api/v1/subscriptions/", headers=auth_headers(user_a.id))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user_a.id


# ---------------------------------------------------------------------------
# PATCH /api/v1/subscriptions/{id}
# ---------------------------------------------------------------------------

async def test_update_subscription_success(client, db_session):
    """Owner must be able to update the target price."""
    user = await make_user(db_session, email="upd@example.com")
    headers = auth_headers(user.id)

    create_resp = await client.post(
        "/api/v1/subscriptions/",
        json={"url": PRODUCT_URL, "target_price": 50.0},
        headers=headers,
    )
    sub_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/subscriptions/{sub_id}",
        json={"target_price": 30.0},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["target_price"] == 30.0


async def test_update_subscription_not_found(client, db_session):
    """Updating another user's or non-existent subscription must return 404."""
    user = await make_user(db_session, email="notfound@example.com")
    response = await client.patch(
        "/api/v1/subscriptions/99999",
        json={"target_price": 10.0},
        headers=auth_headers(user.id),
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/subscriptions/{id}
# ---------------------------------------------------------------------------

async def test_delete_subscription_success(client, db_session):
    """Owner must be able to delete their subscription, returning 204."""
    user = await make_user(db_session, email="del@example.com")
    headers = auth_headers(user.id)

    create_resp = await client.post(
        "/api/v1/subscriptions/",
        json={"url": PRODUCT_URL, "target_price": 50.0},
        headers=headers,
    )
    sub_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/subscriptions/{sub_id}", headers=headers)
    assert del_resp.status_code == 204

    list_resp = await client.get("/api/v1/subscriptions/", headers=headers)
    assert list_resp.json() == []


async def test_delete_subscription_not_found(client, db_session):
    """Deleting another user's or non-existent subscription must return 404."""
    user = await make_user(db_session, email="delnf@example.com")
    response = await client.delete(
        "/api/v1/subscriptions/99999",
        headers=auth_headers(user.id),
    )
    assert response.status_code == 404
