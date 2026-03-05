"""
测试数据生成相关数据模型
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Float,
    Boolean,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TestDataTask(Base):
    """测试数据生成任务"""

    __tablename__ = "test_data_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    task_name = Column(String(128), nullable=False, comment="任务名称")
    source_datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, comment="源数据源ID（生产数据）")
    target_datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, comment="目标数据源ID（测试数据）")
    data_ratio = Column(Float, default=1.0, comment="数据量比例")
    keep_relations = Column(Boolean, default=True, comment="保持关联关系")
    table_configs = Column(JSON, comment="表配置")
    schedule_type = Column(String(32), default="MANUAL", comment="调度类型：MANUAL/CRON")
    cron_expression = Column(String(128), comment="Cron表达式")
    status = Column(String(32), default="DRAFT", comment="状态：DRAFT/READY/RUNNING/PAUSED")
    created_by = Column(BigInteger, ForeignKey("sys_user.id"), comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    source_datasource = relationship("DataSource", foreign_keys=[source_datasource_id])
    target_datasource = relationship("DataSource", foreign_keys=[target_datasource_id])
    created_by_user = relationship("User", back_populates="created_test_data_tasks")
    profiles = relationship("TestDataProfile", back_populates="task", cascade="all, delete-orphan")
    executions = relationship("TestDataExecution", back_populates="task", cascade="all, delete-orphan")


class TestDataProfile(Base):
    """数据特征配置"""

    __tablename__ = "test_data_profile"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    task_id = Column(BigInteger, ForeignKey("test_data_task.id", ondelete="CASCADE"), nullable=False, comment="任务ID")
    table_name = Column(String(128), nullable=False, comment="表名")
    column_name = Column(String(128), nullable=False, comment="列名")
    data_type = Column(String(64), comment="数据类型")
    profile_type = Column(String(32), comment="特征类型：DISTRIBUTION/PATTERN/LOOKUP")
    profile_data = Column(JSON, comment="特征数据")
    generator_type = Column(String(64), comment="生成器类型")
    generator_params = Column(JSON, comment="生成器参数")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    task = relationship("TestDataTask", back_populates="profiles")


class TestDataExecution(Base):
    """测试数据生成执行记录"""

    __tablename__ = "test_data_execution"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="执行ID")
    task_id = Column(BigInteger, ForeignKey("test_data_task.id", ondelete="CASCADE"), nullable=False, comment="任务ID")
    execution_no = Column(String(32), comment="执行编号")
    trigger_type = Column(String(32), default="MANUAL", comment="触发类型：MANUAL/SCHEDULE")
    status = Column(String(32), default="PENDING", comment="状态：PENDING/RUNNING/SUCCESS/FAILED")
    total_tables = Column(BigInteger, default=0, comment="总表数")
    completed_tables = Column(BigInteger, default=0, comment="完成表数")
    total_records = Column(BigInteger, default=0, comment="总记录数")
    success_records = Column(BigInteger, default=0, comment="成功记录数")
    failed_records = Column(BigInteger, default=0, comment="失败记录数")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    task = relationship("TestDataTask", back_populates="executions")
