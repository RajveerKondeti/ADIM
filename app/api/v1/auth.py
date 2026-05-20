from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, require_role, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegister, UserResponse
from app.schemas.auth import UserLogin
from app.api.deps import get_current_user

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(body: UserRegister, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email,
        password=hash_password(body.password),
        role="user",  # Default role is user, not admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT",
)
def login(body: UserLogin, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == body.email).first()

    # Single error message — don't tell the caller whether email or password was wrong.
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return {
        "access_token": create_access_token(subject=user.email),
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get(
    "/admin-only",
    summary="Admin-only test endpoint",
)
def admin_only(current_user: User = Depends(get_current_user)) -> dict:
    require_role(current_user, "admin")
    return {"message": f"Welcome, Admin {current_user.email}"}