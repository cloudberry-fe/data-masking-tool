"""
翻数工具相关数据模型
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DataSyncTask(Base):
    """翻数任务表"""

    __tablename__ = "data_sync_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    task_name = Column(String(128), nullable=False, comment="任务名称")
    source_datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, comment="源数据源ID")
    target_datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, comment="目标数据源ID")
    sync_mode = Column(String(32), default="FULL", comment="同步模式：FULL/INCREMENTAL")
    table_mapping = Column(JSON, comment="表映射配置")
    schedule_type = Column(String(32), default="MANUAL", comment="调度类型：MANUAL/CRON")
    cron_expression = Column(String(128), comment="Cron表达式")
    status = Column(String(32), default="DRAFT", comment="状态：DRAFT/READY/RUNNING/PAUSED")
    created_by = Column(BigInteger, ForeignKey("sys_user.id"), comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    source_datasource = relationship("DataSource", foreign_keys=[source_datasource_id], back_populates="source_sync_tasks")
    target_datasource = relationship("DataSource", foreign_keys=[target_datasource_id], back_populates="target_sync_tasks")
    created_by_user = relationship("User", back_populates="created_sync_tasks")
