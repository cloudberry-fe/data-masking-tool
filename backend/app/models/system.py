"""
用户权限相关数据模型
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Integer,
    SmallInteger,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """用户表"""

    __tablename__ = "sys_user"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(64), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(256), nullable=False, comment="密码哈希")
    real_name = Column(String(64), comment="真实姓名")
    email = Column(String(128), comment="邮箱")
    phone = Column(String(32), comment="手机号")
    status = Column(SmallInteger, default=1, comment="状态：0-禁用，1-启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("Role", secondary="sys_user_role", viewonly=True)
    created_datasources = relationship("DataSource", back_populates="created_by_user")
    created_masking_tasks = relationship("MaskingTask", back_populates="created_by_user")
    created_masking_templates = relationship("MaskingTemplate", back_populates="created_by_user")
    created_sync_tasks = relationship("DataSyncTask", back_populates="created_by_user")
    created_test_data_tasks = relationship("TestDataTask", back_populates="created_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Role(Base):
    """角色表"""

    __tablename__ = "sys_role"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="角色ID")
    role_code = Column(String(64), unique=True, nullable=False, comment="角色编码")
    role_name = Column(String(64), nullable=False, comment="角色名称")
    description = Column(String(512), comment="角色描述")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    users = relationship("User", secondary="sys_user_role", viewonly=True)
    permissions = relationship("Permission", secondary="sys_role_permission", viewonly=True)


class Permission(Base):
    """权限表"""

    __tablename__ = "sys_permission"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="权限ID")
    permission_code = Column(String(128), unique=True, nullable=False, comment="权限编码")
    permission_name = Column(String(128), nullable=False, comment="权限名称")
    resource_type = Column(String(32), comment="资源类型")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class UserRole(Base):
    """用户角色关联表"""

    __tablename__ = "sys_user_role"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    user_id = Column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")
    role_id = Column(BigInteger, ForeignKey("sys_role.id"), nullable=False, comment="角色ID")

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uk_user_role"),)

    # 关联
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


class RolePermission(Base):
    """角色权限关联表"""

    __tablename__ = "sys_role_permission"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    role_id = Column(BigInteger, ForeignKey("sys_role.id"), nullable=False, comment="角色ID")
    permission_id = Column(BigInteger, ForeignKey("sys_permission.id"), nullable=False, comment="权限ID")

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uk_role_permission"),)

    # 关联
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
