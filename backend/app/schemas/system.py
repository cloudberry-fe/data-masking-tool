"""
系统管理相关Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from app.schemas.common import TimestampMixin


# ==================== 用户相关 ====================

class UserBase(BaseModel):
    """用户基础信息"""

    username: str = Field(..., min_length=1, max_length=64, description="用户名")
    real_name: Optional[str] = Field(default=None, max_length=64, description="真实姓名")
    email: Optional[str] = Field(default=None, max_length=128, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=32, description="手机号")


class UserCreate(UserBase):
    """创建用户"""

    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserUpdate(BaseModel):
    """更新用户"""

    real_name: Optional[str] = Field(default=None, max_length=64)
    email: Optional[str] = Field(default=None, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=32)
    status: Optional[int] = Field(default=None, description="状态")


class UserResponse(UserBase, TimestampMixin):
    """用户响应"""

    id: int
    status: int
    roles: List["RoleResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(UserResponse):
    """用户列表响应（不包含敏感信息）"""
    pass


# ==================== 角色相关 ====================

class RoleBase(BaseModel):
    """角色基础信息"""

    role_code: str = Field(..., min_length=1, max_length=64, description="角色编码")
    role_name: str = Field(..., min_length=1, max_length=64, description="角色名称")
    description: Optional[str] = Field(default=None, max_length=512, description="角色描述")


class RoleCreate(RoleBase):
    """创建角色"""
    pass


class RoleUpdate(BaseModel):
    """更新角色"""

    role_name: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = Field(default=None, max_length=512)


class RoleResponse(RoleBase):
    """角色响应"""

    id: int
    created_at: Optional[datetime] = None
    permissions: List["PermissionResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==================== 权限相关 ====================

class PermissionResponse(BaseModel):
    """权限响应"""

    id: int
    permission_code: str
    permission_name: str
    resource_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 关联操作 ====================

class UserRoleAssign(BaseModel):
    """用户角色分配"""

    user_id: int = Field(..., description="用户ID")
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")


class RolePermissionAssign(BaseModel):
    """角色权限分配"""

    role_id: int = Field(..., description="角色ID")
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")


# 更新前向引用
UserResponse.model_rebuild()
RoleResponse.model_rebuild()
