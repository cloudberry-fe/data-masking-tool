"""
认证服务
"""
import logging
from typing import Optional, Tuple
from datetime import timedelta, datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.models.system import User, Role, Permission
from app.schemas.auth import LoginResponse

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        stmt = select(User).where(User.username == username)
        user = db.scalar(stmt)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.status != 1:
            return None
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        stmt = select(User).where(User.id == user_id)
        return db.scalar(stmt)

    @staticmethod
    def get_user_permissions(db: Session, user: User) -> list:
        """获取用户权限列表"""
        stmt = (
            select(Permission)
            .join(Role.permissions)
            .join(UserRole)
            .where(UserRole.user_id == user.id)
            .distinct()
        )
        permissions = db.scalars(stmt).all()
        return [p.permission_code for p in permissions]

    @staticmethod
    def get_user_roles(db: Session, user: User) -> list:
        """获取用户角色列表"""
        stmt = (
            select(Role)
            .join(User.roles)
            .where(User.id == user.id)
        )
        roles = db.scalars(stmt).all()
        return [{"id": r.id, "code": r.role_code, "name": r.role_name} for r in roles]

    @staticmethod
    def create_login_response(user: User, roles: list, permissions: list) -> LoginResponse:
        """创建登录响应"""
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires,
        )
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            username=user.username,
            real_name=user.real_name,
            roles=roles,
            permissions=permissions,
        )

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> Tuple[bool, str]:
        """修改密码"""
        if not verify_password(old_password, user.password_hash):
            return False, "原密码错误"
        user.password_hash = get_password_hash(new_password)
        db.add(user)
        db.commit()
        return True, "密码修改成功"

    @staticmethod
    def init_default_data(db: Session):
        """初始化默认数据"""
        # 检查是否已有管理员用户
        stmt = select(User).where(User.username == "admin")
        admin = db.scalar(stmt)
        if admin:
            logger.info("默认数据已存在，跳过初始化")
            return

        logger.info("开始初始化默认数据...")

        # 创建默认权限
        permissions_data = [
            ("datasource:view", "数据源查看", "datasource"),
            ("datasource:create", "数据源创建", "datasource"),
            ("datasource:update", "数据源编辑", "datasource"),
            ("datasource:delete", "数据源删除", "datasource"),
            ("masking:view", "脱敏任务查看", "masking"),
            ("masking:create", "脱敏任务创建", "masking"),
            ("masking:update", "脱敏任务编辑", "masking"),
            ("masking:execute", "脱敏任务执行", "masking"),
            ("masking:delete", "脱敏任务删除", "masking"),
            ("lineage:view", "血缘分析查看", "lineage"),
            ("sync:view", "翻数任务查看", "sync"),
            ("sync:create", "翻数任务创建", "sync"),
            ("sync:execute", "翻数任务执行", "sync"),
            ("system:user", "用户管理", "system"),
            ("system:role", "角色管理", "system"),
            ("system:audit", "审计日志", "system"),
        ]

        permissions = []
        for code, name, res_type in permissions_data:
            perm = Permission(permission_code=code, permission_name=name, resource_type=res_type)
            db.add(perm)
            permissions.append(perm)

        db.flush()

        # 创建管理员角色
        admin_role = Role(
            role_code="admin",
            role_name="超级管理员",
            description="拥有所有权限的系统管理员"
        )
        db.add(admin_role)
        db.flush()

        # 给管理员角色分配所有权限
        from app.models.system import RolePermission
        for perm in permissions:
            rp = RolePermission(role_id=admin_role.id, permission_id=perm.id)
            db.add(rp)

        # 创建普通用户角色
        user_role = Role(
            role_code="user",
            role_name="普通用户",
            description="普通用户角色"
        )
        db.add(user_role)

        # 创建管理员用户
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            real_name="系统管理员",
            email="admin@example.com",
            status=1,
        )
        db.add(admin_user)
        db.flush()

        # 给管理员用户分配角色
        from app.models.system import UserRole
        ur = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        db.add(ur)

        db.commit()
        logger.info("默认数据初始化完成！")
        logger.info("默认账号: admin / admin123")
