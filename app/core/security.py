"""
security.py — everything authentication-related lives here.

Consolidates what was previously split across:
  - app/core/jwt.py        (token creation)
  - app/core/security.py   (bcrypt hashing)
  - app/core/roles.py      (role guard)

Single responsibility: if it touches auth, it lives here.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
import bcrypt

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
# passlib manages the bcrypt context cleanly — no manual salt/encode gymnastics.
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
    
# ── JWT tokens ────────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Args:
        subject: Typically the user's email — becomes the "sub" claim.
        expires_delta: Override default expiry for specific use cases.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str:
    """
    Decodes a JWT and returns the subject (email).
    Raises HTTP 401 on any failure — invalid signature, expired, malformed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject: str | None = payload.get("sub")
        if subject is None:
            raise credentials_exception
        return subject
    except JWTError:
        raise credentials_exception


# ── Role guard ────────────────────────────────────────────────────────────────

def require_role(user, required_role: str) -> None:
    """
    Raises 403 if the user doesn't have the required role.
    Usage:  require_role(current_user, "admin")
    """
    if user.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires the '{required_role}' role.",
        )