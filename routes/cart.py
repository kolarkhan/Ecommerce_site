from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from core.security import get_current_user
from core.config import cart_collection
from core.config import products


router = APIRouter(prefix="/cart", tags=["Cart"])

# ---------------------- ADD PRODUCT TO CART ----------------------
@router.post("/add/{product_id}")
async def add_to_cart(product_id: str, user: dict = Depends(get_current_user)):
    """
    🛒 Add a product to the user's cart.
    """
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_item = cart_collection.find_one({"user_email": user["sub"], "product_id": product_id})

    if existing_item:
        cart_collection.update_one(
            {"_id": existing_item["_id"]},
            {"$inc": {"quantity": 1}}
        )
    else:
        cart_collection.insert_one({
            "user_email": user["sub"],
            "product_id": product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": 1
        })

    return {"message": "✅ Product added to cart successfully"}


# ---------------------- GET USER CART ----------------------
@router.get("/")
async def get_cart(user: dict = Depends(get_current_user)):
    """
    🧾 Get all items in the user's cart.
    """
    items = list(cart_collection.find({"user_email": user["sub"]}))
    for item in items:
        item["_id"] = str(item["_id"])
    return {"cart_items": items, "total_items": len(items)}


# ---------------------- UPDATE ITEM QUANTITY ----------------------
@router.put("/update/{product_id}")
async def update_cart_item(product_id: str, quantity: int, user: dict = Depends(get_current_user)):
    """
    🔄 Update the quantity of a specific product in the user's cart.
    """
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    result = cart_collection.update_one(
        {"user_email": user["sub"], "product_id": product_id},
        {"$set": {"quantity": quantity}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Product not found in cart")

    return {"message": "✅ Cart updated successfully"}


# ---------------------- REMOVE PRODUCT FROM CART ----------------------
@router.delete("/remove/{product_id}")
async def remove_from_cart(product_id: str, user: dict = Depends(get_current_user)):
    """
    ❌ Remove a specific product from the user's cart.
    """
    result = cart_collection.delete_one({"user_email": user["sub"], "product_id": product_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    return {"message": "🗑️ Product removed from cart"}


# ---------------------- CLEAR ENTIRE CART ----------------------
@router.delete("/clear")
async def clear_cart(user: dict = Depends(get_current_user)):
    """
    🧹 Remove all items from the user's cart.
    """
    cart_collection.delete_many({"user_email": user["sub"]})
    return {"message": "🧺 Cart cleared successfully"}

