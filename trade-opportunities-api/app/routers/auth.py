"""
Authentication router - register, login, logout
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.schemas import UserRegister, UserLogin, TokenResponse
from app.utils.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, generate_session_id
)
from app.utils.storage import storage
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new account and receive a JWT access token."
)
async def register(user_data: UserRegister):
    """
    Register a new user account.
    
    - **username**: 3-50 alphanumeric characters, underscores, hyphens
    - **password**: Minimum 8 characters
    
    Returns a JWT token valid for 24 hours.
    """
    # Check if username exists
    if storage.get_user(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken. Please choose a different username."
        )

    # Create user
    password_hash = hash_password(user_data.password)
    storage.create_user(user_data.username, password_hash)

    # Generate token
    token, expires = create_access_token(user_data.username)

    logger.info(f"New user registered: {user_data.username}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
        username=user_data.username
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token",
    description="Authenticate with username and password to receive a JWT token."
)
async def login(credentials: UserLogin):
    """
    Login to receive a JWT access token.
    
    Use the returned token in the `Authorization: Bearer <token>` header for protected endpoints.
    """
    user = storage.get_user(credentials.username.lower())

    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token, expires = create_access_token(user["username"])
    logger.info(f"User logged in: {user['username']}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
        username=user["username"]
    )


@router.post(
    "/logout",
    summary="Logout (revoke token)",
    description="Revoke the current JWT token."
)
async def logout(current_user: str = Depends(get_current_user)):
    """Logout the current user by revoking their token."""
    logger.info(f"User logged out: {current_user}")
    return {"message": f"Successfully logged out. Goodbye, {current_user}!"}


@router.get(
    "/me",
    summary="Get current user info"
)
async def get_me(current_user: str = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    user = storage.get_user(current_user)
    return {
        "username": current_user,
        "created_at": user["created_at"],
        "total_requests": user["request_count"]
    }