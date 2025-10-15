from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from core.security import get_current_user
from core.config import products, wishlist_collection, cart_collection

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])



# ---------------------- ADD TO WISHLIST ----------------------
@router.post("/add/{product_id}")
async def add_to_wishlist(product_id: str, user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if wishlist_collection.find_one({"user_email": user["sub"], "product_id": product_id}):
        raise HTTPException(status_code=400, detail="Product already in wishlist")

    wishlist_collection.insert_one({
        "user_email": user["sub"],
        "product_id": product_id,
        "name": product["name"],
        "price": product["price"]
    })
    return {"message": "✅ Product added to wishlist"}


# ---------------------- GET USER WISHLIST ----------------------
@router.get("/")
async def get_wishlist(user: dict = Depends(get_current_user)):
    items = list(wishlist_collection.find({"user_email": user["sub"]}))
    for item in items:
        item["_id"] = str(item["_id"])
    return {"wishlist": items, "total_items": len(items)}


# ---------------------- REMOVE FROM WISHLIST ----------------------
@router.delete("/remove/{product_id}")
async def remove_from_wishlist(product_id: str, user: dict = Depends(get_current_user)):
    result = wishlist_collection.delete_one({"user_email": user["sub"], "product_id": product_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in wishlist")

    return {"message": "🗑️ Product removed from wishlist"}


# ---------------------- MOVE FROM WISHLIST → CART ----------------------
@router.post("/move-to-cart/{product_id}")
async def move_to_cart(product_id: str, user: dict = Depends(get_current_user)):
    """
    🔄 Move a product from wishlist to cart.
    - Removes item from wishlist
    - Adds it to cart (or increases quantity if already present)
    """
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    # Find the wishlist item
    wishlist_item = wishlist_collection.find_one({"user_email": user["sub"], "product_id": product_id})
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")

    # Check if product exists in DB
    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in database")

    # Add to cart (or increase quantity)
    existing_cart_item = cart_collection.find_one({"user_email": user["sub"], "product_id": product_id})
    if existing_cart_item:
        cart_collection.update_one(
            {"_id": existing_cart_item["_id"]},
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

    # Remove from wishlist
    wishlist_collection.delete_one({"_id": wishlist_item["_id"]})

    return {"message": f"✅ '{product['name']}' moved from wishlist to cart"}