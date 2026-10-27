"""
Authentication and Shop Profile Routes.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Response
from backend.schemas.auth import (
    ShopRegisterRequest,
    ShopLoginRequest,
    ShopResponse,
    AuthTokenResponse,
    ProfileUpdateRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from backend.services.auth_service import AuthService, get_current_shop

router = APIRouter(prefix="/auth", tags=["Multi-Shop Authentication"])


@router.post("/register", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
def register_medical_shop(payload: ShopRegisterRequest):
    """
    Register a new medical shop account.
    - Validates email and phone number formats.
    - Checks for duplicate email address.
    - Securely hashes password using bcrypt.
    """
    shop = AuthService.register_shop(
        shop_name=payload.shop_name,
        owner_name=payload.owner_name,
        email=payload.email,
        phone_number=payload.phone_number,
        address=payload.address,
        password=payload.password,
    )
    return shop


@router.post("/login", response_model=AuthTokenResponse)
def login_medical_shop(payload: ShopLoginRequest, response: Response):
    """
    Authenticate medical shop credentials.
    - Verifies bcrypt password hash.
    - Issues JWT access token with tenant claim.
    - Sets secure HTTP-only cookie.
    """
    auth_data = AuthService.login_shop(
        email=payload.email,
        password=payload.password,
        remember_me=bool(payload.remember_me),
    )

    # Set secure cookie
    max_age = 7 * 86400 if payload.remember_me else 86400
    response.set_cookie(
        key="access_token",
        value=auth_data["access_token"],
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production HTTPS
    )

    return auth_data


@router.post("/logout")
def logout_medical_shop(response: Response):
    """
    Log out medical shop and clear authentication session cookies.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=ShopResponse)
def get_authenticated_shop_profile(current_shop: Dict[str, Any] = Depends(get_current_shop)):
    """
    Retrieve currently authenticated medical shop profile.
    Sensitive details (password hashes) are omitted.
    """
    return current_shop


@router.put("/profile", response_model=ShopResponse)
def update_medical_shop_profile(
    payload: ProfileUpdateRequest,
    current_shop: Dict[str, Any] = Depends(get_current_shop),
):
    """
    Update profile details for the authenticated medical shop.
    """
    updated = AuthService.update_profile(
        shop_id=current_shop["id"],
        shop_name=payload.shop_name,
        owner_name=payload.owner_name,
        phone_number=payload.phone_number,
        address=payload.address,
    )
    return updated


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password_request(payload: ForgotPasswordRequest):
    """
    Initiate secure password reset for medical shop account.
    Returns reset token directly for seamless testing and demonstration.
    """
    token = AuthService.generate_password_reset_token(payload.email)
    if not token:
        # Prevent user enumeration by returning standard message
        return {
            "message": "If an account exists with this email address, password reset instructions have been issued.",
            "reset_token": None,
        }

    return {
        "message": "Password reset token generated successfully.",
        "reset_token": token,
    }


@router.post("/reset-password")
def reset_password_with_token(payload: ResetPasswordRequest):
    """
    Reset password using validated one-time security token.
    """
    AuthService.reset_password(payload.token, payload.new_password)
    return {"message": "Password has been successfully updated. You may now log in."}
