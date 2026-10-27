"""
Pydantic Schemas for Multi-Shop Authentication & User Management.
Uses dependency-free regex email validation.
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class ShopRegisterRequest(BaseModel):
    shop_name: str = Field(..., min_length=2, max_length=150, description="Name of the pharmacy/shop")
    owner_name: str = Field(..., min_length=2, max_length=100, description="Name of the shop owner")
    email: str = Field(..., description="Unique email address for authentication")
    phone_number: str = Field(..., min_length=7, max_length=20, description="Contact telephone number")
    address: str = Field(..., min_length=3, max_length=250, description="Physical address of the medical shop")
    password: str = Field(..., min_length=6, max_length=100, description="Password (minimum 6 characters)")
    confirm_password: str = Field(..., min_length=6, max_length=100, description="Password confirmation")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean.lower()

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Password and confirmation password do not match.")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = "".join(ch for ch in v if ch.isdigit() or ch in "+-() ")
        digits_only = "".join(ch for ch in cleaned if ch.isdigit())
        if len(digits_only) < 7:
            raise ValueError("Phone number must contain at least 7 digits.")
        return v.strip()


class ShopLoginRequest(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")
    remember_me: Optional[bool] = Field(False, description="Extend session duration")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean.lower()


class ShopResponse(BaseModel):
    id: str
    shop_name: str
    owner_name: str
    email: str
    phone_number: str
    address: str
    account_status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    shop: ShopResponse


class ProfileUpdateRequest(BaseModel):
    shop_name: Optional[str] = Field(None, min_length=2, max_length=150)
    owner_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=7, max_length=20)
    address: Optional[str] = Field(None, min_length=3, max_length=250)


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean.lower()


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None  # Returned for easy local demonstration/testing


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New password and confirmation password do not match.")
        return v
