"""
Authentication utilities: password hashing, JWT tokens, and user database operations.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Configuration ────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_change_me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

ADMIN_SECRET = "admin123"  # Required to register as admin

# ── Password hashing context ────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── HTTP Bearer scheme ───────────────────────────────────────────
security = HTTPBearer()

# ── Database path (shared with vectorstore) ──────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
METADATA_DB_PATH = os.path.join(DATA_DIR, "metadata.db")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with embedded user data."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ── User Database Operations ────────────────────────────────────
def create_user(username: str, password: str, role: str = "employee") -> dict:
    """Create a new user in the database. Returns user dict."""
    conn = sqlite3.connect(METADATA_DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, hashed_password, role, created_at) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), role, datetime.utcnow().isoformat()),
        )
        conn.commit()
        user_id = cur.lastrowid
        return {"id": user_id, "username": username, "role": role}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    """Retrieve a user by username."""
    conn = sqlite3.connect(METADATA_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, hashed_password, role FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "hashed_password": row[2], "role": row[3]}
    return None


# ── FastAPI Dependencies ─────────────────────────────────────────
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency: extract and validate the current user from JWT."""
    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    role = payload.get("role")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"username": username, "role": role}


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency: ensure the current user is an admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
