"""
数据脱敏相关数据模型
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MaskingTask(Base):
    """脱敏任务表"""

    __tablename__ = "masking_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    task_name = Column(String(128), nullable=False, comment="任务名称")
    task_code = Column(String(64), unique=True, index=True, comment="任务编码")
    description = Column(Text, comment="任务描述")
    datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, comment="数据源ID")
    source_schema = Column(String(128), comment="源Schema")
    target_schema = Column(String(128), comment="目标Schema")
    task_type = Column(String(32), default="TABLE", comment="任务类型")
    schedule_type = Column(String(32), default="MANUAL", comment="调度类型：MANUAL/CRON")
    cron_expression = Column(String(128), comment="Cron表达式")
    status = Column(String(32), default="DRAFT", comment="状态：DRAFT/READY/RUNNING/PAUSED")
    created_by = Column(BigInteger, ForeignKey("sys_user.id"), comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    datasource = relationship("DataSource", back_populates="masking_tasks")
    created_by_user = relationship("User", back_populates="created_masking_tasks")
    tables = relationship("MaskingTable", back_populates="task", cascade="all, delete-orphan", order_by="MaskingTable.order_no")
    executions = relationship("MaskingTaskExecution", back_populates="task", cascade="all, delete-orphan")


class MaskingTable(Base):
    """脱敏表配置表"""

    __tablename__ = "masking_table"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    task_id = Column(BigInteger, ForeignKey("masking_task.id"), nullable=False, index=True, comment="任务ID")
    table_name = Column(String(128), nullable=False, comment="表名")
    source_table = Column(String(128), comment="源表名")
    target_table = Column(String(128), comment="目标表名")
    order_no = Column(Integer, default=0, comment="执行顺序")
    enabled = Column(Boolean, default=True, comment="是否启用")

    # 关联
    task = relationship("MaskingTask", back_populates="tables")
    columns = relationship("MaskingColumn", back_populates="table", cascade="all, delete-orphan")


class MaskingColumn(Base):
    """脱敏字段配置表"""

    __tablename__ = "masking_column"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    table_id = Column(BigInteger, ForeignKey("masking_table.id"), nullable=False, index=True, comment="表配置ID")
    column_name = Column(String(128), nullable=False, comment="字段名")
    data_type = Column(String(64), comment="数据类型")
    masking_algorithm = Column(String(64), nullable=False, comment="脱敏算法")
    algorithm_params = Column(JSON, comment="算法参数")
    description = Column(String(512), comment="说明")

    # 关联
    table = relationship("MaskingTable", back_populates="columns")


class MaskingTemplate(Base):
    """脱敏规则模板表"""

    __tablename__ = "masking_template"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="模板ID")
    template_name = Column(String(128), nullable=False, comment="模板名称")
    template_code = Column(String(64), unique=True, index=True, comment="模板编码")
    description = Column(Text, comment="模板描述")
    config_json = Column(JSON, comment="模板配置")
    created_by = Column(BigInteger, ForeignKey("sys_user.id"), comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    created_by_user = relationship("User", back_populates="created_masking_templates")


class MaskingTaskExecution(Base):
    """脱敏任务执行记录表"""

    __tablename__ = "masking_task_execution"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="执行ID")
    task_id = Column(BigInteger, ForeignKey("masking_task.id"), nullable=False, index=True, comment="任务ID")
    execution_no = Column(String(64), unique=True, index=True, comment="执行编号")
    trigger_type = Column(String(32), default="MANUAL", comment="触发类型：MANUAL/SCHEDULE")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    status = Column(String(32), default="PENDING", comment="状态：PENDING/RUNNING/SUCCESS/FAILED/PARTIAL")
    total_records = Column(BigInteger, default=0, comment="总记录数")
    success_records = Column(BigInteger, default=0, comment="成功记录数")
    failed_records = Column(BigInteger, default=0, comment="失败记录数")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    task = relationship("MaskingTask", back_populates="executions")
