"""
认证API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.schemas.common import Response
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
)
from app.schemas.system import UserResponse
from app.services.auth_service import AuthService
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=Response[LoginResponse])
def login(
    request: LoginRequest,
    db: DBSession,
    audit: AuditLogger,
):
    """用户登录"""
    user = AuthService.authenticate_user(db, request.username, request.password)
    if not user:
        audit("LOGIN", "auth", f"登录失败: {request.username}", "FAIL")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    roles = AuthService.get_user_roles(db, user)
    permissions = AuthService.get_user_permissions(db, user)
    login_response = AuthService.create_login_response(user, roles, permissions)

    audit("LOGIN", "auth", f"登录成功: {request.username}")
    return Response(data=login_response)


@router.post("/logout", response_model=Response)
def logout(
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """用户登出"""
    audit("LOGOUT", "auth", f"登出: {current_user.username}")
    return Response(message="登出成功")


@router.get("/current-user", response_model=Response[UserResponse])
def get_current_user_info(
    current_user: CurrentUser,
    db: DBSession,
):
    """获取当前用户信息"""
    user = AuthService.get_user_with_roles(db, current_user.id)
    return Response(data=user)


@router.put("/change-password", response_model=Response)
def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DBSession,
    audit: AuditLogger,
):
    """修改密码"""
    success, message = AuthService.change_password(
        db, current_user, request.old_password, request.new_password
    )
    if not success:
        audit("UPDATE", "auth", f"修改密码失败: {message}", "FAIL")
        raise HTTPException(status_code=400, detail=message)

    audit("UPDATE", "auth", "修改密码成功")
    return Response(message=message)
