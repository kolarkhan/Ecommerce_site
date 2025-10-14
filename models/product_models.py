from pydantic import BaseModel
from typing import Optional

class ProductModel(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    in_stock: int
