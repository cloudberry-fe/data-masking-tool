"""
数据脱敏相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from datetime import datetime
from app.schemas.common import TimestampMixin


# 脱敏算法定义
MASKING_ALGORITHMS = [
    {"code": "REPLACE", "name": "替换", "description": "使用固定值或随机值替换"},
    {"code": "MASK", "name": "掩码", "description": "保留部分信息，其他用掩码"},
    {"code": "HASH", "name": "哈希", "description": "单向哈希不可逆"},
    {"code": "ENCRYPT", "name": "加密", "description": "可逆加密"},
    {"code": "ROUND", "name": "取整", "description": "数值范围取整"},
    {"code": "OFFSET", "name": "偏移", "description": "数值固定偏移"},
    {"code": "SHUFFLE", "name": "洗牌", "description": "数据内部洗牌"},
    {"code": "NULL", "name": "空值", "description": "置为NULL"},
    {"code": "SUBSTITUTION", "name": "字典替换", "description": "使用字典数据替换"},
    {"code": "PRESERVATION", "name": "格式保持", "description": "保持格式的脱敏"},
]


class MaskingAlgorithm(BaseModel):
    """脱敏算法"""

    code: str = Field(..., description="算法编码")
    name: str = Field(..., description="算法名称")
    description: Optional[str] = Field(default=None, description="算法描述")


# ==================== 脱敏任务 ====================

class MaskingTaskBase(BaseModel):
    """脱敏任务基础"""

    task_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="任务名称",
        validation_alias=AliasChoices('task_name', 'taskName'),
        serialization_alias='taskName'
    )
    task_code: Optional[str] = Field(
        default=None,
        max_length=64,
        description="任务编码",
        validation_alias=AliasChoices('task_code', 'taskCode'),
        serialization_alias='taskCode'
    )
    description: Optional[str] = Field(default=None, description="任务描述")
    datasource_id: int = Field(
        ...,
        description="数据源ID",
        validation_alias=AliasChoices('datasource_id', 'datasourceId'),
        serialization_alias='datasourceId'
    )
    source_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        description="源Schema",
        validation_alias=AliasChoices('source_schema', 'sourceSchema'),
        serialization_alias='sourceSchema'
    )
    target_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        description="目标Schema",
        validation_alias=AliasChoices('target_schema', 'targetSchema'),
        serialization_alias='targetSchema'
    )
    task_type: str = Field(
        default="TABLE",
        description="任务类型",
        validation_alias=AliasChoices('task_type', 'taskType'),
        serialization_alias='taskType'
    )
    schedule_type: str = Field(
        default="MANUAL",
        description="调度类型：MANUAL/CRON",
        validation_alias=AliasChoices('schedule_type', 'scheduleType'),
        serialization_alias='scheduleType'
    )
    cron_expression: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Cron表达式",
        validation_alias=AliasChoices('cron_expression', 'cronExpression'),
        serialization_alias='cronExpression'
    )


class MaskingTaskCreate(MaskingTaskBase):
    """创建脱敏任务"""
    pass


class MaskingTaskUpdate(BaseModel):
    """更新脱敏任务"""

    task_name: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('task_name', 'taskName'),
        serialization_alias='taskName'
    )
    description: Optional[str] = None
    source_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('source_schema', 'sourceSchema'),
        serialization_alias='sourceSchema'
    )
    target_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('target_schema', 'targetSchema'),
        serialization_alias='targetSchema'
    )
    schedule_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('schedule_type', 'scheduleType'),
        serialization_alias='scheduleType'
    )
    cron_expression: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('cron_expression', 'cronExpression'),
        serialization_alias='cronExpression'
    )
    status: Optional[str] = None


class MaskingTaskResponse(MaskingTaskBase, TimestampMixin):
    """脱敏任务响应"""

    id: int
    status: str
    created_by: Optional[int] = Field(
        default=None,
        serialization_alias='createdBy'
    )
    tables: List["MaskingTableResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 脱敏表配置 ====================

class MaskingTableBase(BaseModel):
    """脱敏表基础"""

    table_name: str = Field(
        ...,
        max_length=128,
        description="表名",
        validation_alias=AliasChoices('table_name', 'tableName'),
        serialization_alias='tableName'
    )
    source_table: Optional[str] = Field(
        default=None,
        max_length=128,
        description="源表名",
        validation_alias=AliasChoices('source_table', 'sourceTable'),
        serialization_alias='sourceTable'
    )
    target_table: Optional[str] = Field(
        default=None,
        max_length=128,
        description="目标表名",
        validation_alias=AliasChoices('target_table', 'targetTable'),
        serialization_alias='targetTable'
    )
    order_no: int = Field(
        default=0,
        description="执行顺序",
        validation_alias=AliasChoices('order_no', 'orderNo'),
        serialization_alias='orderNo'
    )
    enabled: bool = Field(default=True, description="是否启用")


class MaskingTableCreate(MaskingTableBase):
    """创建脱敏表"""

    task_id: int = Field(
        ...,
        description="任务ID",
        validation_alias=AliasChoices('task_id', 'taskId'),
        serialization_alias='taskId'
    )


class MaskingTableUpdate(BaseModel):
    """更新脱敏表"""

    source_table: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('source_table', 'sourceTable'),
        serialization_alias='sourceTable'
    )
    target_table: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('target_table', 'targetTable'),
        serialization_alias='targetTable'
    )
    order_no: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices('order_no', 'orderNo'),
        serialization_alias='orderNo'
    )
    enabled: Optional[bool] = None


class MaskingTableResponse(MaskingTableBase):
    """脱敏表响应"""

    id: int
    task_id: int = Field(
        serialization_alias='taskId'
    )
    columns: List["MaskingColumnResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 脱敏字段配置 ====================

class MaskingColumnBase(BaseModel):
    """脱敏字段基础"""

    column_name: str = Field(
        ...,
        max_length=128,
        description="字段名",
        validation_alias=AliasChoices('column_name', 'columnName'),
        serialization_alias='columnName'
    )
    data_type: Optional[str] = Field(
        default=None,
        max_length=64,
        description="数据类型",
        validation_alias=AliasChoices('data_type', 'dataType'),
        serialization_alias='dataType'
    )
    masking_algorithm: str = Field(
        ...,
        max_length=64,
        description="脱敏算法",
        validation_alias=AliasChoices('masking_algorithm', 'maskingAlgorithm'),
        serialization_alias='maskingAlgorithm'
    )
    algorithm_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="算法参数",
        validation_alias=AliasChoices('algorithm_params', 'algorithmParams'),
        serialization_alias='algorithmParams'
    )
    description: Optional[str] = Field(default=None, max_length=512, description="说明")


class MaskingColumnCreate(MaskingColumnBase):
    """创建脱敏字段"""

    table_id: int = Field(
        ...,
        description="表配置ID",
        validation_alias=AliasChoices('table_id', 'tableId'),
        serialization_alias='tableId'
    )


class MaskingColumnUpdate(BaseModel):
    """更新脱敏字段"""

    data_type: Optional[str] = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices('data_type', 'dataType'),
        serialization_alias='dataType'
    )
    masking_algorithm: Optional[str] = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices('masking_algorithm', 'maskingAlgorithm'),
        serialization_alias='maskingAlgorithm'
    )
    algorithm_params: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices('algorithm_params', 'algorithmParams'),
        serialization_alias='algorithmParams'
    )
    description: Optional[str] = Field(default=None, max_length=512)


class MaskingColumnResponse(MaskingColumnBase):
    """脱敏字段响应"""

    id: int
    table_id: int = Field(
        serialization_alias='tableId'
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 脱敏模板 ====================

class MaskingTemplateBase(BaseModel):
    """脱敏模板基础"""

    template_name: str = Field(
        ...,
        max_length=128,
        description="模板名称",
        validation_alias=AliasChoices('template_name', 'templateName'),
        serialization_alias='templateName'
    )
    template_code: Optional[str] = Field(
        default=None,
        max_length=64,
        description="模板编码",
        validation_alias=AliasChoices('template_code', 'templateCode'),
        serialization_alias='templateCode'
    )
    description: Optional[str] = Field(default=None, description="模板描述")
    config_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="模板配置",
        validation_alias=AliasChoices('config_json', 'configJson'),
        serialization_alias='configJson'
    )


class MaskingTemplateCreate(MaskingTemplateBase):
    """创建脱敏模板"""
    pass


class MaskingTemplateResponse(MaskingTemplateBase, TimestampMixin):
    """脱敏模板响应"""

    id: int
    created_by: Optional[int] = Field(
        default=None,
        serialization_alias='createdBy'
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 任务执行 ====================

class MaskingTaskExecutionResponse(BaseModel):
    """脱敏任务执行记录响应"""

    id: int
    task_id: int = Field(
        serialization_alias='taskId'
    )
    execution_no: str = Field(
        serialization_alias='executionNo'
    )
    trigger_type: str = Field(
        serialization_alias='triggerType'
    )
    start_time: Optional[datetime] = Field(
        default=None,
        serialization_alias='startTime'
    )
    end_time: Optional[datetime] = Field(
        default=None,
        serialization_alias='endTime'
    )
    status: str
    total_records: int = Field(
        default=0,
        serialization_alias='totalRecords'
    )
    success_records: int = Field(
        default=0,
        serialization_alias='successRecords'
    )
    failed_records: int = Field(
        default=0,
        serialization_alias='failedRecords'
    )
    error_message: Optional[str] = Field(
        default=None,
        serialization_alias='errorMessage'
    )
    created_at: datetime = Field(
        serialization_alias='createdAt'
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MaskingTaskExecuteRequest(BaseModel):
    """脱敏任务执行请求"""

    task_id: int = Field(
        ...,
        description="任务ID",
        validation_alias=AliasChoices('task_id', 'taskId'),
        serialization_alias='taskId'
    )
    remark: Optional[str] = Field(default=None, description="备注")


# 更新前向引用
MaskingTaskResponse.model_rebuild()
MaskingTableResponse.model_rebuild()
