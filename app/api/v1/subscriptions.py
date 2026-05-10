from fastapi import APIRouter


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/")
async def create_subscription() -> dict[str, str]:
    return {"message": "Create subscription endpoint is not implemented yet"}


@router.get("/")
async def list_subscriptions() -> dict[str, str]:
    return {"message": "List subscriptions endpoint is not implemented yet"}


@router.patch("/{subscription_id}")
async def update_subscription(subscription_id: int) -> dict[str, str]:
    return {
        "message": f"Update subscription endpoint is not implemented yet: {subscription_id}"
    }


@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: int) -> dict[str, str]:
    return {
        "message": f"Delete subscription endpoint is not implemented yet: {subscription_id}"
    }
