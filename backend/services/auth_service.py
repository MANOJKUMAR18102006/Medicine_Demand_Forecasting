"""
Authentication, Password Hashing, JWT Token Management & Security Service.
"""

import os
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import bcrypt
import jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.database import get_db

SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", 
    "meddemand-enterprise-pharmacy-auth-key-2026-secure-jwt-token"
)
ALGORITHM = "HS256"
DEFAULT_TOKEN_EXPIRE_HOURS = 24
EXTENDED_TOKEN_EXPIRE_DAYS = 7

# Security bearer scheme for Swagger UI & Authorization header
security_bearer = HTTPBearer(auto_error=False)


class AuthService:
    """Enterprise authentication and session management for Medical Shops."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain text password securely using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against stored bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False

    @staticmethod
    def create_access_token(shop_id: str, email: str, remember_me: bool = False) -> str:
        """Generate signed JWT access token with expiration timestamp."""
        now = datetime.now(timezone.utc)
        if remember_me:
            expires = now + timedelta(days=EXTENDED_TOKEN_EXPIRE_DAYS)
        else:
            expires = now + timedelta(hours=DEFAULT_TOKEN_EXPIRE_HOURS)

        payload = {
            "sub": shop_id,
            "email": email,
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any]:
        """Decode and validate JWT access token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token signature.",
            )

    @classmethod
    def register_shop(
        cls,
        shop_name: str,
        owner_name: str,
        email: str,
        phone_number: str,
        address: str,
        password: str,
    ) -> Dict[str, Any]:
        """Register a new medical shop with unique email check and password hashing."""
        email_clean = email.strip().lower()

        with get_db() as conn:
            cursor = conn.cursor()

            # Check duplicate email
            cursor.execute(
                "SELECT id FROM medical_shops WHERE email = ? COLLATE NOCASE;",
                (email_clean,),
            )
            existing = cursor.fetchone()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A medical shop with email '{email_clean}' is already registered.",
                )

            shop_id = str(uuid.uuid4())
            password_hash = cls.hash_password(password)

            cursor.execute(
                """
                INSERT INTO medical_shops (
                    id, shop_name, owner_name, email, phone_number,
                    address, password_hash, account_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active');
                """,
                (shop_id, shop_name.strip(), owner_name.strip(), email_clean, phone_number.strip(), address.strip(), password_hash),
            )

        return cls.get_shop_by_id(shop_id)

    @classmethod
    def login_shop(cls, email: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        """Authenticate medical shop credentials and issue session JWT token."""
        email_clean = email.strip().lower()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, shop_name, owner_name, email, phone_number,
                       address, password_hash, account_status, created_at, updated_at
                FROM medical_shops
                WHERE email = ? COLLATE NOCASE;
                """,
                (email_clean,),
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        shop = dict(row)

        if shop["account_status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your medical shop account has been deactivated. Please contact support.",
            )

        if not cls.verify_password(password, shop["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        token = cls.create_access_token(shop["id"], shop["email"], remember_me=remember_me)
        # Never expose password hash
        shop.pop("password_hash", None)

        return {
            "access_token": token,
            "token_type": "bearer",
            "shop": shop,
        }

    @classmethod
    def get_shop_by_id(cls, shop_id: str) -> Dict[str, Any]:
        """Retrieve shop profile by unique identifier (excluding password hash)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, shop_name, owner_name, email, phone_number,
                       address, account_status, created_at, updated_at
                FROM medical_shops
                WHERE id = ?;
                """,
                (shop_id,),
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical shop not found.",
            )
        return dict(row)

    @classmethod
    def update_profile(
        cls,
        shop_id: str,
        shop_name: Optional[str] = None,
        owner_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update authenticated shop profile details."""
        updates = []
        params = []
        if shop_name is not None:
            updates.append("shop_name = ?")
            params.append(shop_name.strip())
        if owner_name is not None:
            updates.append("owner_name = ?")
            params.append(owner_name.strip())
        if phone_number is not None:
            updates.append("phone_number = ?")
            params.append(phone_number.strip())
        if address is not None:
            updates.append("address = ?")
            params.append(address.strip())

        if not updates:
            return cls.get_shop_by_id(shop_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(shop_id)

        sql = f"UPDATE medical_shops SET {', '.join(updates)} WHERE id = ?;"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))

        return cls.get_shop_by_id(shop_id)

    @classmethod
    def generate_password_reset_token(cls, email: str) -> Optional[str]:
        """Generate a secure one-time password reset token for shop recovery."""
        email_clean = email.strip().lower()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM medical_shops WHERE email = ? COLLATE NOCASE;",
                (email_clean,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            shop_id = row["id"]
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

            cursor.execute(
                """
                INSERT INTO password_resets (token, shop_id, expires_at, used)
                VALUES (?, ?, ?, 0);
                """,
                (token, shop_id, expires_at),
            )
            return token

    @classmethod
    def reset_password(cls, token: str, new_password: str) -> bool:
        """Verify token and update medical shop password securely."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT token, shop_id, expires_at, used
                FROM password_resets
                WHERE token = ?;
                """,
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired password reset token.",
                )

            if row["used"] == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This password reset token has already been used.",
                )

            # Check expiration
            expires_at = datetime.fromisoformat(row["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password reset token has expired. Please request a new one.",
                )

            new_hash = cls.hash_password(new_password)
            cursor.execute(
                "UPDATE medical_shops SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (new_hash, row["shop_id"]),
            )
            cursor.execute(
                "UPDATE password_resets SET used = 1 WHERE token = ?;",
                (token,),
            )

        return True


def get_current_shop(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Dict[str, Any]:
    """
    FastAPI Dependency to authenticate server-side identity.
    Derives authorized shop identity from JWT header or HTTP-only cookie.
    Guarantees that client-supplied shop IDs are never blindly trusted.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = AuthService.decode_access_token(token)
    shop_id = payload.get("sub")
    if not shop_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims. No shop identity found.",
        )

    return AuthService.get_shop_by_id(shop_id)


def get_optional_current_shop(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[Dict[str, Any]]:
    """Optional authentication dependency for backward compatibility."""
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = AuthService.decode_access_token(token)
        shop_id = payload.get("sub")
        if not shop_id:
            return None
        return AuthService.get_shop_by_id(shop_id)
    except Exception:
        return None
