from fastapi import APIRouter, Form, Depends, HTTPException
from core.security import get_current_user
from core.config import users

router = APIRouter()

@router.get("/")
async def get_profile(current_user: dict = Depends(get_current_user)):
    profile = {
        "email": current_user["sub"],
        "verified": current_user.get("verified", False),
        "role": current_user.get("role", "user"),
    }

    db_user = users.find_one({"email": current_user["sub"]}, {"_id": 0, "password": 0})
    if db_user:
        profile.update({
            "name": db_user.get("name"),
            "phone": db_user.get("phone"),
            "address": db_user.get("address"),
        })

    return {"profile": profile}

@router.put("/")
async def update_profile(
    name: str = Form(None),
    phone: str = Form(None),
    address: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    update_data = {}
    if name: update_data["name"] = name
    if phone: update_data["phone"] = phone
    if address: update_data["address"] = address

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = users.update_one({"email": current_user["sub"]}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found or no change made")

    return {"message": "Profile updated successfully"}
