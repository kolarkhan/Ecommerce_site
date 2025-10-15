from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from math import ceil
from core.security import get_current_user, admin_required
from core.config import orders_collection, cart_collection, products
router = APIRouter(prefix="/orders", tags=["Orders"])

# ---------------------- PLACE ORDER ----------------------
@router.post("/place")
async def place_order(user: dict = Depends(get_current_user)):
    """
    ✅ Places an order for all items in the user's cart.
    - Checks stock availability
    - Deducts stock from products
    - Clears user's cart
    """
    cart_items = list(cart_collection.find({"user_email": user["sub"]}))

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Check stock before confirming order
    for item in cart_items:
        product = products.find_one({"_id": ObjectId(item["product_id"])})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['name']} not found")
        if product["in_stock"] < item["quantity"]:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {item['name']}")

    # Place the order
    order_data = {
        "user_email": user["sub"],
        "items": cart_items,
        "total_amount": sum(i["price"] * i["quantity"] for i in cart_items),
        "status": "Delivered",
        "created_at": datetime.utcnow(),
    }
    orders_collection.insert_one(order_data)

    # Decrease stock
    for item in cart_items:
        products.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"in_stock": -item["quantity"]}}
        )

    # Clear the cart
    cart_collection.delete_many({"user_email": user["sub"]})

    return {"message": "✅ Order placed successfully and stock updated"}


# ---------------------- GET USER ORDERS ----------------------
@router.get("/my-orders")
async def get_user_orders(user: dict = Depends(get_current_user)):
    """
    👤 Get all orders of the logged-in user.
    """
    orders = list(orders_collection.find({"user_email": user["sub"]}).sort("created_at", -1))
    for order in orders:
        order["_id"] = str(order["_id"])
        for item in order["items"]:
            item["_id"] = str(item["_id"])
    return {"orders": orders, "total_orders": len(orders)}


# ---------------------- CANCEL ORDER ----------------------
@router.delete("/cancel/{order_id}")
async def cancel_order(order_id: str, user: dict = Depends(get_current_user)):
    """
    ❌ Cancel user's own order (only if still in Processing status)
    """
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = orders_collection.find_one({"_id": ObjectId(order_id), "user_email": user["sub"]})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] != "Processing":
        raise HTTPException(status_code=400, detail="Order cannot be canceled once shipped or delivered")

    orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "Canceled"}}
    )
    return {"message": "🛑 Order canceled successfully"}


# ---------------------- ADMIN: VIEW ALL ORDERS ----------------------
@router.get("/all", dependencies=[Depends(admin_required)])
async def get_all_orders(page: int = 1, limit: int = 10):
    """
    🧾 Admin only — view all orders with pagination.
    """
    skip = (page - 1) * limit
    total_orders = orders_collection.count_documents({})
    total_pages = ceil(total_orders / limit)

    cursor = orders_collection.find().sort("created_at", -1).skip(skip).limit(limit)
    data = []
    for order in cursor:
        order["_id"] = str(order["_id"])
        for item in order["items"]:
            item["_id"] = str(item["_id"])
        data.append(order)

    return {"page": page, "total_pages": total_pages, "orders": data}


# ---------------------- ADMIN: UPDATE ORDER STATUS ----------------------
@router.put("/update-status/{order_id}", dependencies=[Depends(admin_required)])
async def update_order_status(order_id: str, status: str):
    """
    🚚 Admin updates the order status (e.g., Shipped, Delivered, etc.)
    """
    if status not in ["Processing", "Shipped", "Delivered", "Canceled"]:
        raise HTTPException(status_code=400, detail="Invalid status value")

    result = orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"message": f"✅ Order status updated to '{status}'"}