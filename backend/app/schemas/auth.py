"""
Authentication Related Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Login request"""

    username: str = Field(..., description="Username", min_length=1, max_length=64)
    password: str = Field(..., description="Password", min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Login response"""

    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration time (seconds)")
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    real_name: Optional[str] = Field(default=None, description="Real name")
    roles: list = Field(default_factory=list, description="Role list")
    permissions: list = Field(default_factory=list, description="Permission list")


class ChangePasswordRequest(BaseModel):
    """Change password request"""

    old_password: str = Field(..., description="Old password", min_length=1)
    new_password: str = Field(..., description="New password", min_length=6, max_length=128)


class ResetPasswordRequest(BaseModel):
    """Reset password request (admin)"""

    user_id: int = Field(..., description="User ID")
    new_password: str = Field(..., description="New password", min_length=6, max_length=128)
