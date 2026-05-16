"""Integration tests for the /products endpoints."""

import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PriceHistory, Product
from tests.conftest import auth_headers, make_user


async def _create_product(db: AsyncSession, url: str = "https://shop.example.com/item") -> Product:
    """Insert a product directly into the test database."""
    product = Product(
        url=url,
        title="Test Product",
        current_price=99.99,
        last_parsed_at=datetime.datetime.now(datetime.UTC),
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# GET /api/v1/products/{product_id}
# ---------------------------------------------------------------------------

async def test_get_product_not_found(client):
    """Non-existent product must return 404."""
    response = await client.get("/api/v1/products/99999")
    assert response.status_code == 404


async def test_get_product_success(client, db_session):
    """Existing product must return 200 with correct fields."""
    product = await _create_product(db_session)
    response = await client.get(f"/api/v1/products/{product.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product.id
    assert data["url"] == product.url
    assert data["current_price"] == product.current_price


# ---------------------------------------------------------------------------
# GET /api/v1/products/{product_id}/history
# ---------------------------------------------------------------------------

async def test_get_product_history_requires_auth(client, db_session):
    """Price history endpoint must require authentication."""
    product = await _create_product(db_session)
    response = await client.get(f"/api/v1/products/{product.id}/history")
    assert response.status_code == 401


async def test_get_product_history_empty(client, db_session):
    """Product with no history must return an empty list."""
    user = await make_user(db_session, email="hist@example.com")
    product = await _create_product(db_session)
    response = await client.get(
        f"/api/v1/products/{product.id}/history",
        headers=auth_headers(user.id),
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_get_product_history_populated(client, db_session):
    """Price history must be returned ordered by timestamp ascending."""
    user = await make_user(db_session, email="hist2@example.com")
    product = await _create_product(db_session)

    now = datetime.datetime.now(datetime.UTC)
    records = [
        PriceHistory(product_id=product.id, price=p, timestamp=now + datetime.timedelta(seconds=i))
        for i, p in enumerate([50.0, 40.0, 30.0])
    ]
    db_session.add_all(records)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/products/{product.id}/history",
        headers=auth_headers(user.id),
    )
    assert response.status_code == 200
    prices = [r["price"] for r in response.json()]
    assert prices == [50.0, 40.0, 30.0]


async def test_get_product_history_not_found_returns_404(client, db_session):
    """History for a non-existent product must return 404."""
    user = await make_user(db_session, email="hist3@example.com")
    response = await client.get(
        "/api/v1/products/99999/history",
        headers=auth_headers(user.id),
    )
    assert response.status_code == 404
