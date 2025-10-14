from fastapi import FastAPI
from routes import auth_routes, profile_routes, product_routes

app = FastAPI(
    title="E-Commerce API",
    description="Secure E-commerce API with authentication, user profiles, and product management.",
    version="1.0"
)

# Register routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(profile_routes.router, prefix="/profile", tags=["User Profile"])
app.include_router(product_routes.router, prefix="/products", tags=["Products"])
