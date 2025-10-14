from fastapi import APIRouter, Depends, HTTPException
from core.security import admin_required
from core.config import products
from models.product_models import ProductModel

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
