from fastapi import APIRouter


router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}/history")
async def get_product_history(product_id: int) -> dict[str, str]:
    return {
        "message": f"Product history endpoint is not implemented yet: {product_id}"
    }
