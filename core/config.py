import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"
MONGO_URI = os.getenv("MONGO_URI")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TOKEN_EXPIRE_HOURS = int(os.getenv("VERIFICATION_TOKEN_EXPIRE_HOURS", 1))

client = MongoClient(MONGO_URI)
db = client["userdb"]
users = db["users"]
products = db["products"]
wishlist_collection = db["wishlist"]
cart_collection = db["cart"]
orders_collection = db["orders"]
token_blacklist = db["token_blacklist"]
