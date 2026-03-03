"""
系统管理API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.schemas.common import Response, PageResponse
from app.schemas.system import (
    UserResponse,
    UserCreate,
    UserUpdate,
    RoleResponse,
    RoleCreate,
    RoleUpdate,
    PermissionResponse,
    UserRoleAssign,
    RolePermissionAssign,
)
from app.services.user_service import UserService
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


# ==================== 用户管理 ====================

@router.get("/users", response_model=Response[PageResponse[UserResponse]])
def get_users(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    status: Optional[int] = None,
):
    """获取用户列表"""
    users, total = UserService.get_users(db, page, page_size, keyword, status)
    return Response(data=PageResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("/users", response_model=Response[UserResponse])
def create_user(
    request: UserCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建用户"""
    existing = UserService.get_user_by_username(db, request.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = UserService.create_user(
        db,
        username=request.username,
        password=request.password,
        real_name=request.real_name,
        email=request.email,
        phone=request.phone,
    )
    audit("CREATE", "system", f"创建用户: {request.username}")
    return Response(data=user, message="创建成功")


@router.get("/users/{user_id}", response_model=Response[UserResponse])
def get_user(
    user_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取用户详情"""
    user = UserService.get_user_with_roles(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return Response(data=user)


@router.put("/users/{user_id}", response_model=Response[UserResponse])
def update_user(
    user_id: int,
    request: UserUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新用户"""
    user = UserService.update_user(
        db,
        user_id,
        real_name=request.real_name,
        email=request.email,
        phone=request.phone,
        status=request.status,
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    audit("UPDATE", "system", f"更新用户: {user.username}")
    return Response(data=user, message="更新成功")


@router.delete("/users/{user_id}", response_model=Response)
def delete_user(
    user_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = UserService.get_user(db, user_id)
    if user:
        success = UserService.delete_user(db, user_id)
        if success:
            audit("DELETE", "system", f"删除用户: {user.username}")
    return Response(message="删除成功")


@router.put("/users/{user_id}/roles", response_model=Response)
def assign_user_roles(
    user_id: int,
    request: UserRoleAssign,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """分配用户角色"""
    success = UserService.assign_user_roles(db, user_id, request.role_ids)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    audit("UPDATE", "system", f"分配用户角色: 用户ID={user_id}, 角色ID={request.role_ids}")
    return Response(message="分配成功")


# ==================== 角色管理 ====================

@router.get("/roles", response_model=Response[List[RoleResponse]])
def get_roles(
    db: DBSession,
    current_user: CurrentUser,
):
    """获取角色列表"""
    roles = UserService.get_roles(db)
    return Response(data=roles)


@router.post("/roles", response_model=Response[RoleResponse])
def create_role(
    request: RoleCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建角色"""
    role = UserService.create_role(
        db,
        role_code=request.role_code,
        role_name=request.role_name,
        description=request.description,
    )
    audit("CREATE", "system", f"创建角色: {request.role_name}")
    return Response(data=role, message="创建成功")


@router.get("/roles/{role_id}", response_model=Response[RoleResponse])
def get_role(
    role_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取角色详情"""
    role = UserService.get_role_with_permissions(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return Response(data=role)


@router.put("/roles/{role_id}", response_model=Response[RoleResponse])
def update_role(
    role_id: int,
    request: RoleUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新角色"""
    role = UserService.update_role(
        db,
        role_id,
        role_name=request.role_name,
        description=request.description,
    )
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    audit("UPDATE", "system", f"更新角色: {role.role_name}")
    return Response(data=role, message="更新成功")


@router.delete("/roles/{role_id}", response_model=Response)
def delete_role(
    role_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除角色"""
    role = UserService.get_role(db, role_id)
    if role:
        success = UserService.delete_role(db, role_id)
        if success:
            audit("DELETE", "system", f"删除角色: {role.role_name}")
    return Response(message="删除成功")


@router.put("/roles/{role_id}/permissions", response_model=Response)
def assign_role_permissions(
    role_id: int,
    request: RolePermissionAssign,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """分配角色权限"""
    success = UserService.assign_role_permissions(db, role_id, request.permission_ids)
    if not success:
        raise HTTPException(status_code=404, detail="角色不存在")
    audit("UPDATE", "system", f"分配角色权限: 角色ID={role_id}")
    return Response(message="分配成功")


# ==================== 权限管理 ====================

@router.get("/permissions", response_model=Response[List[PermissionResponse]])
def get_permissions(
    db: DBSession,
    current_user: CurrentUser,
):
    """获取所有权限"""
    permissions = UserService.get_permissions(db)
    return Response(data=permissions)
