from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from .config import SECRET_KEY, ALGORITHM
from .config import token_blacklist
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str):
    return pwd_context.hash(password)

def create_token(email: str, expire_hours: int, role="user", verified=False):
    expire = datetime.utcnow() + timedelta(hours=expire_hours)
    payload = {"sub": email, "role": role, "verified": verified, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def admin_required(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user




def revoke_token(token: str):
    token_blacklist.insert_one({"token": token})

def is_token_revoked(token: str) -> bool:
    return token_blacklist.find_one({"token": token}) is not None

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        if is_token_revoked(token):
            raise HTTPException(status_code=401, detail="Token has been revoked. Please log in again.")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
