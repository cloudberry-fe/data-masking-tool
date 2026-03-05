"""
动态脱敏规则模型

动态脱敏是针对表进行配置，为特定数据库角色设置脱敏规则
使用 PostgreSQL Anon 扩展的 SECURITY LABEL 机制
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DynamicMaskingRule(Base):
    """动态脱敏规则 - 针对表配置角色脱敏"""

    __tablename__ = "dynamic_masking_rule"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="规则ID")
    rule_name = Column(String(128), nullable=False, comment="规则名称")
    datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, comment="数据源ID")

    # 表信息
    schema_name = Column(String(128), default="public", comment="Schema名")
    table_name = Column(String(128), nullable=False, comment="表名")

    # 角色配置
    masked_roles = Column(JSON, comment="被脱敏的数据库角色列表")
    exempted_roles = Column(JSON, comment="豁免角色列表(可查看原始数据)")

    # 状态
    status = Column(String(32), default="DRAFT", comment="状态: DRAFT/ACTIVE/INACTIVE/ERROR")
    is_enabled = Column(Boolean, default=False, comment="是否已启用")
    error_message = Column(Text, comment="错误信息")

    # 元数据
    description = Column(Text, comment="描述")
    created_by = Column(BigInteger, ForeignKey("sys_user.id"), comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    datasource = relationship("DataSource")
    created_by_user = relationship("User")
    column_rules = relationship(
        "DynamicMaskingColumnRule",
        back_populates="rule",
        cascade="all, delete-orphan"
    )


class DynamicMaskingColumnRule(Base):
    """动态脱敏字段规则"""

    __tablename__ = "dynamic_masking_column_rule"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    rule_id = Column(BigInteger, ForeignKey("dynamic_masking_rule.id"), nullable=False, index=True, comment="规则ID")

    column_name = Column(String(128), nullable=False, comment="字段名")
    data_type = Column(String(64), comment="数据类型")

    # 脱敏算法
    masking_algorithm = Column(String(128), nullable=False, comment="脱敏算法")
    algorithm_params = Column(JSON, comment="算法参数")

    # 关联
    rule = relationship("DynamicMaskingRule", back_populates="column_rules")


class AnonymizationTask(Base):
    """原地匿名化任务"""

    __tablename__ = "anonymization_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    task_name = Column(String(128), nullable=False, comment="任务名称")
    datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, comment="数据源ID")

    # 表信息
    schema_name = Column(String(128), default="public", comment="Schema名")
    table_name = Column(String(128), nullable=False, comment="表名")

    # 备份配置
    backup_before_anonymize = Column(Boolean, default=True, comment="执行前是否备份")
    backup_table_name = Column(String(128), comment="备份表名")

    # 状态
    status = Column(String(32), default="DRAFT", comment="状态")
    last_executed_at = Column(DateTime, comment="最后执行时间")

    # 元数据
    description = Column(Text, comment="描述")
    created_by = Column(BigInteger, ForeignKey("sys_user.id"), comment="创建人")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    datasource = relationship("DataSource")
    created_by_user = relationship("User")
    column_rules = relationship(
        "AnonymizationColumnRule",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    executions = relationship(
        "AnonymizationExecution",
        back_populates="task",
        cascade="all, delete-orphan"
    )


class AnonymizationColumnRule(Base):
    """匿名化字段规则"""

    __tablename__ = "anonymization_column_rule"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    task_id = Column(BigInteger, ForeignKey("anonymization_task.id"), nullable=False, index=True, comment="任务ID")

    column_name = Column(String(128), nullable=False, comment="字段名")
    data_type = Column(String(64), comment="数据类型")

    # 脱敏算法
    masking_algorithm = Column(String(128), nullable=False, comment="脱敏算法")
    algorithm_params = Column(JSON, comment="算法参数")

    # 关联
    task = relationship("AnonymizationTask", back_populates="column_rules")


class AnonymizationExecution(Base):
    """匿名化执行记录"""

    __tablename__ = "anonymization_execution"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="执行ID")
    task_id = Column(BigInteger, ForeignKey("anonymization_task.id"), nullable=False, index=True, comment="任务ID")

    execution_no = Column(String(64), unique=True, index=True, comment="执行编号")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    status = Column(String(32), default="PENDING", comment="状态")

    total_records = Column(BigInteger, default=0, comment="处理记录数")
    error_message = Column(Text, comment="错误信息")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    task = relationship("AnonymizationTask", back_populates="executions")
