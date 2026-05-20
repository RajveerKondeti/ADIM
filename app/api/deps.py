"""
deps.py — FastAPI dependency injection for shared concerns.

Any route that needs authentication adds:
    current_user: User = Depends(get_current_user)

That's it. All the token decoding, DB lookup, and error handling
is handled here — routes stay clean.
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

http_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts the Bearer token, validates it, and returns the User.
    Raises HTTP 401 automatically on any failure.
    """
    email = decode_access_token(credentials.credentials)

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    return user