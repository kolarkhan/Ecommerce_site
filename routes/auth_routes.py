from fastapi import APIRouter, HTTPException, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from pydantic import EmailStr
from core.security import hash_password, create_token, verify_token
from core.config import users, TOKEN_EXPIRE_HOURS
from core.email_utils import send_email, validate_email_exists
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from core.security import get_current_user, revoke_token
from models.user_models import UserRegister
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
async def register_user(request_data: UserRegister, request: Request):
    email = request_data.email
    
    password = request_data.password

    # Check if user already exists
    if users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="User already registered")

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Save user to database
    users.insert_one({
        
        "email": email,
        "password": hashed_password,
        "role": "user",
        "is_verified": False,
        "created_at": datetime.utcnow()
    })

    # Generate verification token and link
    verification_token = create_token(email, 1)
    verification_link = f"{request.url.scheme}://{request.client.host}:8000/auth/verify/{verification_token}"
    expire_time = datetime.utcnow() + timedelta(hours=1)
    formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

    # Send verification email
    send_email(
        email,
        "Verify Your Account",
        f"Click the link to verify your account: {verification_link}\nExpires at: {formatted_expire_time}",
        f"""
        <html><body>
        <p>Click below to verify your email:</p>
        <a href="{verification_link}" style="padding:10px 20px;background-color:#4CAF50;color:white;border-radius:5px;text-decoration:none;">Verify Email</a>
        <p>This link expires at: {formatted_expire_time}</p>
        </body></html>
        """
    )

    return {"message": "Registration successful! Please check your email for verification link."}

@router.get("/verify/{token}")
async def verify_email(token: str):
    email = verify_token(token)
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["is_verified"]:
        return {"message": "Account already verified."}

    users.update_one({"email": email}, {"$set": {"verified": True}})
    return {"message": "Email verified successfully!"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    user = users.find_one({"email": form_data.username})
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not user.get("is_verified", False):
        token = create_token(user["email"], TOKEN_EXPIRE_HOURS)
        verify_link = f"{request.url.scheme}://{request.client.host}:8000/auth/verify/{token}"
        expire_time = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")
        send_email(
            user["email"],
            "Resend: Verify your account",
            f"Verify here: {verify_link}\nExpires: {formatted_expire_time}",
            f"""
            <html><body>
            <h3>Verify Your Email</h3>
            <p>You attempted to log in but your email is not verified.</p>
            <a href="{verify_link}" style="padding:10px 20px;background-color:#4CAF50;color:white;border-radius:5px;text-decoration:none;">Verify</a>
            <p>This link expires at: {formatted_expire_time}</p>
            </body></html>
            """
        )
        return {"message": "Email not verified. New verification link sent."}

    access_token = create_token(
        email=user["email"],
        expire_hours=1,
        role=user.get("role", "user"),
        verified=True
    )
    return {"access_token": access_token, "token_type": "bearer", "expires_in": "1 hour"}

@router.post("/forgot-password")
async def forgot_password(email: EmailStr, request: Request):
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    reset_token = create_token(email, 1)
    reset_link = f"{request.url.scheme}://{request.client.host}:8000/auth/reset-password/{reset_token}"
    expire_time = datetime.utcnow() + timedelta(hours=1)
    formatted_expire_time = expire_time.strftime("%Y-%m-%d %H:%M UTC")

    send_email(
        email,
        "Reset Your Password",
        f"Reset your password: {reset_link}\nExpires at: {formatted_expire_time}",
        f"""
        <html><body>
        <h3>Password Reset Request</h3>
        <a href="{reset_link}" style="padding:10px 20px;background-color:#FF9800;color:white;border-radius:5px;text-decoration:none;">Reset Password</a>
        <p>This link expires at: {formatted_expire_time}</p>
        </body></html>
        """
    )

    return {"message": "Password reset link sent."}



@router.get("/reset-password/{token}", response_class=HTMLResponse)
async def get_reset_form(token: str):
    try:
        verify_token(token)
    except Exception as e:
        return HTMLResponse(f"<h3 style='color:red;'>Invalid or expired link: {e}</h3>", status_code=400)

    return f"""
    <html><body>
    <h2>Reset Password</h2>
    <form action="/auth/reset-password/{token}" method="post">
        <input type="password" name="new_password" placeholder="Enter new password" required>
        <button type="submit">Reset Password</button>
    </form>
    </body></html>
    """

@router.post("/reset-password/{token}")
async def reset_password(token: str, new_password: str = Form(...)):
    email = verify_token(token)
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = hash_password(new_password)
    users.update_one({"email": email}, {"$set": {"password": hashed_pw}})
    return {"message": "Password reset successful!"}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth2_scheme), current_user: dict = Depends(get_current_user)):
    revoke_token(token)
    return {"message": "Successfully logged out"}