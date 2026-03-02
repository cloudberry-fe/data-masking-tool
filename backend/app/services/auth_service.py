"""
Authentication Service
"""
import logging
from typing import Optional, Tuple
from datetime import timedelta, datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.models.system import User, Role, Permission, UserRole, RolePermission
from app.schemas.auth import LoginResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
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
        """Get user by ID"""
        stmt = select(User).where(User.id == user_id)
        return db.scalar(stmt)

    @staticmethod
    def get_user_permissions(db: Session, user: User) -> list:
        """Get user permission list"""
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
        """Get user role list"""
        stmt = (
            select(Role)
            .join(User.roles)
            .where(User.id == user.id)
        )
        roles = db.scalars(stmt).all()
        return [{"id": r.id, "code": r.role_code, "name": r.role_name} for r in roles]

    @staticmethod
    def create_login_response(user: User, roles: list, permissions: list) -> LoginResponse:
        """Create login response"""
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
        """Change user password"""
        if not verify_password(old_password, user.password_hash):
            return False, "Current password is incorrect"
        user.password_hash = get_password_hash(new_password)
        db.add(user)
        db.commit()
        return True, "Password changed successfully"

    @staticmethod
    def init_default_data(db: Session):
        """Initialize default data"""
        # Check if admin user already exists
        stmt = select(User).where(User.username == "admin")
        admin = db.scalar(stmt)
        if admin:
            logger.info("Default data already exists, skipping initialization")
            return

        logger.info("Starting default data initialization...")

        # Create default permissions
        permissions_data = [
            ("datasource:view", "View Data Sources", "datasource"),
            ("datasource:create", "Create Data Sources", "datasource"),
            ("datasource:update", "Update Data Sources", "datasource"),
            ("datasource:delete", "Delete Data Sources", "datasource"),
            ("masking:view", "View Masking Tasks", "masking"),
            ("masking:create", "Create Masking Tasks", "masking"),
            ("masking:update", "Update Masking Tasks", "masking"),
            ("masking:execute", "Execute Masking Tasks", "masking"),
            ("masking:delete", "Delete Masking Tasks", "masking"),
            ("lineage:view", "View Lineage Analysis", "lineage"),
            ("sync:view", "View Sync Tasks", "sync"),
            ("sync:create", "Create Sync Tasks", "sync"),
            ("sync:execute", "Execute Sync Tasks", "sync"),
            ("system:user", "User Management", "system"),
            ("system:role", "Role Management", "system"),
            ("system:audit", "Audit Logs", "system"),
        ]

        permissions = []
        for code, name, res_type in permissions_data:
            perm = Permission(permission_code=code, permission_name=name, resource_type=res_type)
            db.add(perm)
            permissions.append(perm)

        db.flush()

        # Create admin role
        admin_role = Role(
            role_code="admin",
            role_name="Administrator",
            description="System administrator with all permissions"
        )
        db.add(admin_role)
        db.flush()

        # Assign all permissions to admin role
        for perm in permissions:
            rp = RolePermission(role_id=admin_role.id, permission_id=perm.id)
            db.add(rp)

        # Create regular user role
        user_role = Role(
            role_code="user",
            role_name="Regular User",
            description="Regular user role"
        )
        db.add(user_role)

        # Create admin user
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            real_name="System Administrator",
            email="admin@example.com",
            status=1,
        )
        db.add(admin_user)
        db.flush()

        # Assign role to admin user
        ur = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        db.add(ur)

        db.commit()
        logger.info("Default data initialization completed!")
        logger.info("Default credentials: admin / admin123")
