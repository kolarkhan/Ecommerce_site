# from fastapi import FastAPI, HTTPException, Request, Depends, Form
# from fastapi.responses import HTMLResponse, RedirectResponse
# from pydantic import BaseModel, EmailStr
# from passlib.context import CryptContext
# from jose import jwt, JWTError, ExpiredSignatureError
# from datetime import datetime, timedelta
# from pymongo import MongoClient
# from email.message import EmailMessage
# from fastapi.security import OAuth2PasswordRequestForm
# import smtplib, ssl, os, dns.resolver
# from dotenv import load_dotenv

# # ---------------- CONFIG ----------------
# load_dotenv(dotenv_path="./.env")

# app = FastAPI()
# SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
# ALGORITHM = "HS256"
# MONGO_URI = os.getenv("MONGO_URI")
# EMAIL_SENDER = os.getenv("EMAIL_SENDER")
# EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# TOKEN_EXPIRE_HOURS = int(os.getenv("VERIFICATION_TOKEN_EXPIRE_HOURS", 1))

# client = MongoClient(MONGO_URI)
# db = client["userdb"]
# users = db["users"]

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # ---------------- MODELS ----------------
# class UserRegister(BaseModel):
#     email: EmailStr
#     password: str

# # ---------------- UTILS ----------------
# def hash_password(password: str):
#     return pwd_context.hash(password)

# def create_token(email: str, expire_hours: int):
#     expire = datetime.utcnow() + timedelta(hours=expire_hours)
#     payload = {"sub": email, "exp": expire}
#     return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# def verify_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload.get("sub")
#     except ExpiredSignatureError:
#         raise HTTPException(status_code=400, detail="Link expired. Please try again.")
#     except JWTError:
#         raise HTTPException(status_code=400, detail="Invalid or tampered token.")

# def validate_email_exists(email: str) -> bool:
#     try:
#         domain = email.split('@')[1]
#         records = dns.resolver.resolve(domain, 'MX')
#         return len(records) > 0
#     except Exception:
#         return False

# def send_email(recipient: str, subject: str, text_body: str, html_body: str):
#     msg = EmailMessage()
#     msg["Subject"] = subject
#     msg["From"] = EMAIL_SENDER
#     msg["To"] = recipient
#     msg.set_content(text_body)
#     msg.add_alternative(html_body, subtype="html")

#     context = ssl.create_default_context()
#     with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
#         smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
#         smtp.send_message(msg)

# # ---------------- ROUTES ----------------

# @app.post("/register")
# async def register_user(user: UserRegister, request: Request):
#     if not validate_email_exists(user.email):
#         raise HTTPException(status_code=400, detail="Invalid or non-existent email domain.")
#     if users.find_one({"email": user.email}):
#         raise HTTPException(status_code=400, detail="Email already registered")

#     hashed_pw = hash_password(user.password)
#     users.insert_one({
#         "email": user.email,
#         "password": hashed_pw,
        
#         "verified": False,
#         "created_at": datetime.utcnow()
#     })

#     token = create_token(user.email, TOKEN_EXPIRE_HOURS)
#     verify_link = f"{request.url.scheme}://{request.client.host}:8000/verify/{token}"

#     expire_time = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
#     formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

#     send_email(
#         user.email,
#         "Verify your account",
#         f"Verify here: {verify_link}\nExpires: {formatted_expire_time}",
#         f"""
#         <html>
#           <body>
#             <h3>Verify Your Email</h3>
#             <p>Click below to verify:</p>
#             <a href="{verify_link}" style="padding:10px 20px;background-color:#4CAF50;color:white;border-radius:5px;text-decoration:none;">Verify</a>
#             <p>This link expires at: {formatted_expire_time}</p>
#           </body>
#         </html>
#         """
#     )

#     return {"message": "User registered successfully. Check your email for verification link."}


# @app.get("/verify/{token}")
# async def verify_email(token: str):
#     email = verify_token(token)
#     user = users.find_one({"email": email})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if user["verified"]:
#         return {"message": "Account already verified."}

#     users.update_one({"email": email}, {"$set": {"verified": True}})
#     return {"message": "Email verified successfully!"}


# @app.post("/login")
# async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
#     user = users.find_one({"email": form_data.username})
#     if not user or not pwd_context.verify(form_data.password, user["password"]):
#         raise HTTPException(status_code=400, detail="Invalid email or password")

#     # Handle unverified users: resend verification link
#     if not user.get("verified", False):
#         token = create_token(user["email"], TOKEN_EXPIRE_HOURS)
#         verify_link = f"{request.url.scheme}://{request.client.host}:8000/verify/{token}"

#         expire_time = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
#         formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

#         send_email(
#             user["email"],
#             "Resend: Verify your account",
#             f"Verify here: {verify_link}\nExpires: {formatted_expire_time}",
#             f"""
#             <html>
#               <body>
#                 <h3>Verify Your Email</h3>
#                 <p>You attempted to log in but your email is not verified.</p>
#                 <p>Click below to verify your account:</p>
#                 <a href="{verify_link}" style="padding:10px 20px;background-color:#4CAF50;color:white;border-radius:5px;text-decoration:none;">Verify</a>
#                 <p>This link expires at: {formatted_expire_time}</p>
#               </body>
#             </html>
#             """
#         )

#         return {
#             "message": "Email not verified. A new verification link has been sent to your email."
#         }

#     # Verified → proceed with normal login
#     access_token = create_token(user["email"], 1)
#     return {"access_token": access_token, "token_type": "bearer", "expires_in": "1 hour"}


# # ---------------- FORGOT PASSWORD ----------------

# @app.post("/forgot-password")
# async def forgot_password(email: EmailStr, request: Request):
#     user = users.find_one({"email": email})
#     if not user:
#         raise HTTPException(status_code=404, detail="Email not found")

#     reset_token = create_token(email, 1)  # expires in 1 hour
#     reset_link = f"{request.url.scheme}://{request.client.host}:8000/reset-password/{reset_token}"

#     expire_time = datetime.utcnow() + timedelta(hours=1)
#     formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

#     send_email(
#         email,
#         "Reset Your Password",
#         f"Reset your password using this link: {reset_link}\nExpires at: {formatted_expire_time}",
#         f"""
#         <html>
#           <body>
#             <h3>Password Reset Request</h3>
#             <p>Click below to reset your password:</p>
#             <a href="{reset_link}" style="padding:10px 20px;background-color:#FF9800;color:white;border-radius:5px;text-decoration:none;">Reset Password</a>
#             <p>This link expires at: {formatted_expire_time}</p>
#           </body>
#         </html>
#         """
#     )

#     return {"message": "Password reset link sent to your email."}


# # ✅ FIXED: Add GET handler so email link opens properly
# @app.get("/reset-password/{token}", response_class=HTMLResponse)
# async def get_reset_password_form(token: str):
#     try:
#         verify_token(token)
#     except Exception as e:
#         return HTMLResponse(f"<h3 style='color:red;'>Invalid or expired link: {e}</h3>", status_code=400)

#     # simple inline HTML form
#     return f"""
#     <html>
#       <body style="font-family:sans-serif;">
#         <h2>🔑 Reset Password</h2>
#         <form action="/reset-password/{token}" method="post">
#           <input type="password" name="new_password" placeholder="Enter new password" required>
#           <button type="submit">Reset Password</button>
#         </form>
#       </body>
#     </html>
#     """


# @app.post("/reset-password/{token}")
# async def reset_password(token: str, new_password: str = Form(...)):
#     email = verify_token(token)
#     user = users.find_one({"email": email})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     hashed_pw = hash_password(new_password)
#     users.update_one({"email": email}, {"$set": {"password": hashed_pw}})

#     return {"message": "Password reset successful!"}









from fastapi import FastAPI, HTTPException, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from pymongo import MongoClient
from email.message import EmailMessage
from fastapi.security import OAuth2PasswordRequestForm
import smtplib, ssl, os, dns.resolver
from dotenv import load_dotenv
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
# ---------------- CONFIG ----------------
load_dotenv(dotenv_path="./.env")

app = FastAPI()
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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# ---------------- MODELS ----------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class ProductModel(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    in_stock: int

# ---------------- UTILS ----------------
def hash_password(password: str):
    return pwd_context.hash(password)

def create_token(email: str, expire_hours: int, role: str = "user", verified: bool = False):
    expire = datetime.utcnow() + timedelta(hours=expire_hours)
    payload = {
        "sub": email,
        "role": role,
        "verified": verified,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Link expired. Please try again.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or tampered token.")

def validate_email_exists(email: str) -> bool:
    try:
        domain = email.split('@')[1]
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except Exception:
        return False

def send_email(recipient: str, subject: str, text_body: str, html_body: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ---------------- ROUTES ----------------

@app.post("/register")
async def register_user(user: UserRegister, request: Request):
    if not validate_email_exists(user.email):
        raise HTTPException(status_code=400, detail="Invalid or non-existent email domain.")
    if users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    users.insert_one({
        "email": user.email,
        "password": hashed_pw,
        "role": "user",
        "verified": False,
        "created_at": datetime.utcnow()
    })

    token = create_token(user.email, TOKEN_EXPIRE_HOURS)
    verify_link = f"{request.url.scheme}://{request.client.host}:8000/verify/{token}"

    expire_time = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

    send_email(
        user.email,
        "Verify your account",
        f"Verify here: {verify_link}\nExpires: {formatted_expire_time}",
        f"""
        <html>
          <body>
            <h3>Verify Your Email</h3>
            <p>Click below to verify:</p>
            <a href="{verify_link}" style="padding:10px 20px;background-color:#4CAF50;color:white;border-radius:5px;text-decoration:none;">Verify</a>
            <p>This link expires at: {formatted_expire_time}</p>
          </body>
        </html>
        """
    )

    return {"message": "User registered successfully. Check your email for verification link."}


@app.get("/verify/{token}")
async def verify_email(token: str):
    email = verify_token(token)
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["verified"]:
        return {"message": "Account already verified."}

    users.update_one({"email": email}, {"$set": {"verified": True}})
    return {"message": "Email verified successfully!"}


@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    user = users.find_one({"email": form_data.username})
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Handle unverified users: resend verification link
    if not user.get("verified", False):
        token = create_token(user["email"], TOKEN_EXPIRE_HOURS)
        verify_link = f"{request.url.scheme}://{request.client.host}:8000/verify/{token}"

        expire_time = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

        send_email(
            user["email"],
            "Resend: Verify your account",
            f"Verify here: {verify_link}\nExpires: {formatted_expire_time}",
            f"""
            <html>
              <body>
                <h3>Verify Your Email</h3>
                <p>You attempted to log in but your email is not verified.</p>
                <p>Click below to verify your account:</p>
                <a href="{verify_link}" style="padding:10px 20px;background-color:#4CAF50;color:white;border-radius:5px;text-decoration:none;">Verify</a>
                <p>This link expires at: {formatted_expire_time}</p>
              </body>
            </html>
            """
        )

        return {
            "message": "Email not verified. A new verification link has been sent to your email."
        }

    # Verified → proceed with normal login
    access_token = create_token(
        email=user["email"],
        expire_hours=1,
        role=user.get("role", "user"),
        verified=user.get("verified", False)
        )

    return {"access_token": access_token, "token_type": "bearer", "expires_in": "1 hour"}


# ---------------- FORGOT PASSWORD ----------------

@app.post("/forgot-password")
async def forgot_password(email: EmailStr, request: Request):
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    reset_token = create_token(email, 1)  # expires in 1 hour
    reset_link = f"{request.url.scheme}://{request.client.host}:8000/reset-password/{reset_token}"

    expire_time = datetime.utcnow() + timedelta(hours=1)
    formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

    send_email(
        email,
        "Reset Your Password",
        f"Reset your password using this link: {reset_link}\nExpires at: {formatted_expire_time}",
        f"""
        <html>
          <body>
            <h3>Password Reset Request</h3>
            <p>Click below to reset your password:</p>
            <a href="{reset_link}" style="padding:10px 20px;background-color:#FF9800;color:white;border-radius:5px;text-decoration:none;">Reset Password</a>
            <p>This link expires at: {formatted_expire_time}</p>
          </body>
        </html>
        """
    )

    return {"message": "Password reset link sent to your email."}


# ✅ FIXED: Add GET handler so email link opens properly
@app.get("/reset-password/{token}", response_class=HTMLResponse)
async def get_reset_password_form(token: str):
    try:
        verify_token(token)
    except Exception as e:
        return HTMLResponse(f"<h3 style='color:red;'>Invalid or expired link: {e}</h3>", status_code=400)

    # simple inline HTML form
    return f"""
    <html>
      <body style="font-family:sans-serif;">
        <h2>🔑 Reset Password</h2>
        <form action="/reset-password/{token}" method="post">
          <input type="password" name="new_password" placeholder="Enter new password" required>
          <button type="submit">Reset Password</button>
        </form>
      </body>
    </html>
    """


@app.post("/reset-password/{token}")
async def reset_password(token: str, new_password: str = Form(...)):
    email = verify_token(token)
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = hash_password(new_password)
    users.update_one({"email": email}, {"$set": {"password": hashed_pw}})

    return {"message": "Password reset successful!"}



# ---------------- AUTH HELPERS ----------------


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # contains email, role, verified
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def admin_required(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ---------------- PROFILE ROUTES ----------------
@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Return the currently logged-in user's profile.
    No MongoDB query — data comes from the JWT token.
    """
    profile = {
        "email": current_user["sub"],  # email is stored as 'sub' in JWT
        "verified": current_user.get("verified", False),
        "role": current_user.get("role", "user"),
    }

    # Optional: also return profile fields from DB (name, phone, address)
    db_user = users.find_one({"email": current_user["sub"]}, {"_id": 0, "password": 0})
    if db_user:
        profile.update({
            "name": db_user.get("name"),
            "phone": db_user.get("phone"),
            "address": db_user.get("address"),
        })

    return {"profile": profile}


@app.put("/profile")
async def update_profile(
    name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Update name, phone, or address for the logged-in user.
    Only touches MongoDB when a change is made.
    """
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


# ---------------- PRODUCT ROUTES ----------------


@app.get("/products")
async def list_products():
    """
    Public endpoint — anyone can view the product list.
    """
    data = list(products.find({}, {"_id": 0}))
    return {"products": data}


@app.post("/products")
async def add_product(
    product: ProductModel,
    admin: dict = Depends(admin_required)
):
    """
    Admin-only endpoint — add a new product.
    """
    products.insert_one(product.dict())
    return {"message": "Product added successfully"}


@app.put("/products/{name}")
async def update_product(
    name: str,
    product: ProductModel,
    admin: dict = Depends(admin_required)
):
    """
    Admin-only endpoint — update an existing product.
    """
    result = products.update_one({"name": name}, {"$set": product.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}


@app.delete("/products/{name}")
async def delete_product(
    name: str,
    admin: dict = Depends(admin_required)
):
    """
    Admin-only endpoint — delete a product.
    """
    result = products.delete_one({"name": name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}