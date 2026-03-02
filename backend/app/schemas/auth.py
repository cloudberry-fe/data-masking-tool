"""
认证相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(..., description="用户名", min_length=1, max_length=64)
    password: str = Field(..., description="密码", min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """登录响应"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    real_name: Optional[str] = Field(default=None, description="真实姓名")
    roles: list = Field(default_factory=list, description="角色列表")
    permissions: list = Field(default_factory=list, description="权限列表")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str = Field(..., description="旧密码", min_length=1)
    new_password: str = Field(..., description="新密码", min_length=6, max_length=128)


class ResetPasswordRequest(BaseModel):
    """重置密码请求（管理员）"""

    user_id: int = Field(..., description="用户ID")
    new_password: str = Field(..., description="新密码", min_length=6, max_length=128)
