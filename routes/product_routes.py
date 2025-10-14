from fastapi import APIRouter, Depends, HTTPException, Query
from core.security import admin_required
from core.config import products
from models.product_models import ProductModel
from typing import Optional
from math import ceil

router = APIRouter()

@router.get("/")
async def list_products():
    data = list(products.find({}, {"_id": 0}))
    return {"products": data}

@router.post("/")
async def add_product(product: ProductModel, admin: dict = Depends(admin_required)):
    products.insert_one(product.dict())
    return {"message": "Product added successfully"}

@router.put("/{name}")
async def update_product(name: str, product: ProductModel, admin: dict = Depends(admin_required)):
    result = products.update_one({"name": name}, {"$set": product.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}

@router.delete("/{name}")
async def delete_product(name: str, admin: dict = Depends(admin_required)):
    result = products.delete_one({"name": name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}



# @router.get("/pagination")
# async def get_products(page: int = Query(1, ge=1, description="Page number")):
#     """
#     Simple pagination: user provides page number.
#     Each page shows 10 products.
#     """
#     limit = 10  # fixed products per page
#     skip = (page - 1) * limit

#     total_products = products.count_documents({})
#     total_pages = (total_products + limit - 1) // limit  # round up pages

#     if page > total_pages and total_products > 0:
#         raise HTTPException(status_code=404, detail="Page not found")

#     cursor = products.find().skip(skip).limit(limit)
#     data = []
#     for item in cursor:
#         item["_id"] = str(item["_id"])
#         data.append(item)

#     return {
        
#         "products": data
#     }




@router.get("/filters")
async def filter_products(
    page: int = Query(1, ge=1, description="Page number"),
    name: Optional[str] = Query(None, description="Search by product name"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Only show in-stock items"),
    category: Optional[str] = Query(None, description="Filter by category")  # 🆕
):
    """
    ✅ Filter + Pagination Endpoint
    Supports:
      - Search by name
      - Filter by price range
      - Filter by stock availability
      - Filter by category
      - Returns paginated results (10 per page)
    """
    limit = 10
    skip = (page - 1) * limit

    # --- Build dynamic MongoDB query ---
    query = {}

    if name:
        query["name"] = {"$regex": name, "$options": "i"}  # case-insensitive
    if min_price is not None and max_price is not None:
        query["price"] = {"$gte": min_price, "$lte": max_price}
    elif min_price is not None:
        query["price"] = {"$gte": min_price}
    elif max_price is not None:
        query["price"] = {"$lte": max_price}
    if in_stock is not None:
        query["in_stock"] = {"$gt": 0} if in_stock else {"$lte": 0}
    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}  # exact match (case-insensitive)

    # --- Pagination + Query Execution ---
    total_products = products.count_documents(query)
    total_pages = ceil(total_products / limit) if total_products > 0 else 1

    if page > total_pages and total_products > 0:
        raise HTTPException(status_code=404, detail="Page not found")

    cursor = products.find(query).skip(skip).limit(limit)
    data = []
    for item in cursor:
        item["_id"] = str(item["_id"])
        data.append(item)

    return {
        
        "products": data
    }
