"""
用户服务
"""
import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, and_, or_, func

from app.core.security import get_password_hash
from app.models.system import User, Role, Permission, UserRole, RolePermission

logger = logging.getLogger(__name__)


class UserService:
    """用户服务"""

    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """获取用户"""
        stmt = select(User).where(User.id == user_id)
        return db.scalar(stmt)

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        stmt = select(User).where(User.username == username)
        return db.scalar(stmt)

    @staticmethod
    def get_users(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[int] = None,
    ) -> Tuple[List[User], int]:
        """获取用户列表"""
        query = select(User)

        if keyword:
            query = query.where(
                or_(
                    User.username.contains(keyword),
                    User.real_name.contains(keyword),
                )
            )
        if status is not None:
            query = query.where(User.status == status)

        # 查询总数
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_stmt)

        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        users = db.scalars(query).all()

        return users, total

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        password: str,
        real_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """创建用户"""
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            real_name=real_name,
            email=email,
            phone=phone,
            status=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        real_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        status: Optional[int] = None,
    ) -> Optional[User]:
        """更新用户"""
        user = UserService.get_user(db, user_id)
        if not user:
            return None

        if real_name is not None:
            user.real_name = real_name
        if email is not None:
            user.email = email
        if phone is not None:
            user.phone = phone
        if status is not None:
            user.status = status

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """删除用户"""
        user = UserService.get_user(db, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def assign_user_roles(db: Session, user_id: int, role_ids: List[int]) -> bool:
        """分配用户角色"""
        user = UserService.get_user(db, user_id)
        if not user:
            return False

        # 删除旧的角色关联
        db.query(UserRole).filter(UserRole.user_id == user_id).delete()

        # 添加新的角色关联
        for role_id in role_ids:
            ur = UserRole(user_id=user_id, role_id=role_id)
            db.add(ur)

        db.commit()
        return True

    @staticmethod
    def get_user_with_roles(db: Session, user_id: int) -> Optional[User]:
        """获取用户及其角色"""
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        return db.scalar(stmt)

    # ==================== 角色相关 ====================

    @staticmethod
    def get_role(db: Session, role_id: int) -> Optional[Role]:
        """获取角色"""
        stmt = select(Role).where(Role.id == role_id)
        return db.scalar(stmt)

    @staticmethod
    def get_roles(db: Session) -> List[Role]:
        """获取角色列表"""
        stmt = select(Role).order_by(Role.created_at.desc())
        return db.scalars(stmt).all()

    @staticmethod
    def create_role(
        db: Session,
        role_code: str,
        role_name: str,
        description: Optional[str] = None,
    ) -> Role:
        """创建角色"""
        role = Role(
            role_code=role_code,
            role_name=role_name,
            description=description,
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def update_role(
        db: Session,
        role_id: int,
        role_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Role]:
        """更新角色"""
        role = UserService.get_role(db, role_id)
        if not role:
            return None

        if role_name is not None:
            role.role_name = role_name
        if description is not None:
            role.description = description

        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def delete_role(db: Session, role_id: int) -> bool:
        """删除角色"""
        role = UserService.get_role(db, role_id)
        if not role:
            return False
        db.delete(role)
        db.commit()
        return True

    @staticmethod
    def assign_role_permissions(db: Session, role_id: int, permission_ids: List[int]) -> bool:
        """分配角色权限"""
        role = UserService.get_role(db, role_id)
        if not role:
            return False

        # 删除旧的权限关联
        db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

        # 添加新的权限关联
        for permission_id in permission_ids:
            rp = RolePermission(role_id=role_id, permission_id=permission_id)
            db.add(rp)

        db.commit()
        return True

    @staticmethod
    def get_role_with_permissions(db: Session, role_id: int) -> Optional[Role]:
        """获取角色及其权限"""
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return db.scalar(stmt)

    # ==================== 权限相关 ====================

    @staticmethod
    def get_permissions(db: Session) -> List[Permission]:
        """获取所有权限"""
        stmt = select(Permission).order_by(Permission.resource_type, Permission.permission_code)
        return db.scalars(stmt).all()
