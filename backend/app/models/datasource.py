"""
数据源管理相关数据模型
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
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DataSource(Base):
    """数据源表"""

    __tablename__ = "datasource"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="数据源ID")
    datasource_name = Column(String(128), nullable=False, comment="数据源名称")
    datasource_type = Column(String(32), nullable=False, index=True, comment="数据源类型：MPP/ORACLE/MYSQL/DM/GOLDENDB")
    host = Column(String(256), comment="主机地址")
    port = Column(Integer, comment="端口")
    database_name = Column(String(128), comment="数据库名")
    username = Column(String(128), comment="用户名")
    password_encrypted = Column(Text, comment="加密密码")
    config_json = Column(JSON, comment="扩展配置")
    enable_account_mapping = Column(Boolean, default=False, comment="是否启用账号映射")
    status = Column(SmallInteger, default=1, comment="状态：0-禁用，1-启用")
    created_by = Column(BigInteger, ForeignKey("sys_user.id"), comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    created_by_user = relationship("User", back_populates="created_datasources")
    references = relationship("DataSourceReference", back_populates="datasource", cascade="all, delete-orphan")
    account_mappings = relationship("AccountMapping", back_populates="datasource", cascade="all, delete-orphan")
    masking_tasks = relationship("MaskingTask", back_populates="datasource")
    source_sync_tasks = relationship("DataSyncTask", foreign_keys="DataSyncTask.source_datasource_id", back_populates="source_datasource")
    target_sync_tasks = relationship("DataSyncTask", foreign_keys="DataSyncTask.target_datasource_id", back_populates="target_datasource")
    lineages = relationship("DataLineage", back_populates="datasource")


class DataSourceReference(Base):
    """数据源引用表"""

    __tablename__ = "datasource_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, index=True, comment="数据源ID")
    reference_type = Column(String(32), comment="引用类型：ENV/PROJECT/TASK")
    reference_id = Column(String(128), comment="引用对象ID")
    reference_name = Column(String(128), comment="引用对象名称")
    created_at = Column(DateTime, server_default=func.now(), comment="引用时间")

    # 关联
    datasource = relationship("DataSource", back_populates="references")


class AccountMapping(Base):
    """账号映射表"""

    __tablename__ = "account_mapping"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, index=True, comment="数据源ID")
    source_account = Column(String(128), comment="源账号")
    target_account = Column(String(128), comment="目标账号")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    datasource = relationship("DataSource", back_populates="account_mappings")
