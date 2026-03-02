"""
数据脱敏相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
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

    task_name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    task_code: Optional[str] = Field(default=None, max_length=64, description="任务编码")
    description: Optional[str] = Field(default=None, description="任务描述")
    datasource_id: int = Field(..., description="数据源ID")
    source_schema: Optional[str] = Field(default=None, max_length=128, description="源Schema")
    target_schema: Optional[str] = Field(default=None, max_length=128, description="目标Schema")
    task_type: str = Field(default="TABLE", description="任务类型")
    schedule_type: str = Field(default="MANUAL", description="调度类型：MANUAL/CRON")
    cron_expression: Optional[str] = Field(default=None, max_length=128, description="Cron表达式")


class MaskingTaskCreate(MaskingTaskBase):
    """创建脱敏任务"""
    pass


class MaskingTaskUpdate(BaseModel):
    """更新脱敏任务"""

    task_name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = None
    source_schema: Optional[str] = Field(default=None, max_length=128)
    target_schema: Optional[str] = Field(default=None, max_length=128)
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = Field(default=None, max_length=128)
    status: Optional[str] = None


class MaskingTaskResponse(MaskingTaskBase, TimestampMixin):
    """脱敏任务响应"""

    id: int
    status: str
    created_by: Optional[int] = None
    tables: List["MaskingTableResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==================== 脱敏表配置 ====================

class MaskingTableBase(BaseModel):
    """脱敏表基础"""

    table_name: str = Field(..., max_length=128, description="表名")
    source_table: Optional[str] = Field(default=None, max_length=128, description="源表名")
    target_table: Optional[str] = Field(default=None, max_length=128, description="目标表名")
    order_no: int = Field(default=0, description="执行顺序")
    enabled: bool = Field(default=True, description="是否启用")


class MaskingTableCreate(MaskingTableBase):
    """创建脱敏表"""

    task_id: int = Field(..., description="任务ID")


class MaskingTableUpdate(BaseModel):
    """更新脱敏表"""

    source_table: Optional[str] = Field(default=None, max_length=128)
    target_table: Optional[str] = Field(default=None, max_length=128)
    order_no: Optional[int] = None
    enabled: Optional[bool] = None


class MaskingTableResponse(MaskingTableBase):
    """脱敏表响应"""

    id: int
    task_id: int
    columns: List["MaskingColumnResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==================== 脱敏字段配置 ====================

class MaskingColumnBase(BaseModel):
    """脱敏字段基础"""

    column_name: str = Field(..., max_length=128, description="字段名")
    data_type: Optional[str] = Field(default=None, max_length=64, description="数据类型")
    masking_algorithm: str = Field(..., max_length=64, description="脱敏算法")
    algorithm_params: Optional[Dict[str, Any]] = Field(default=None, description="算法参数")
    description: Optional[str] = Field(default=None, max_length=512, description="说明")


class MaskingColumnCreate(MaskingColumnBase):
    """创建脱敏字段"""

    table_id: int = Field(..., description="表配置ID")


class MaskingColumnUpdate(BaseModel):
    """更新脱敏字段"""

    data_type: Optional[str] = Field(default=None, max_length=64)
    masking_algorithm: Optional[str] = Field(default=None, max_length=64)
    algorithm_params: Optional[Dict[str, Any]] = None
    description: Optional[str] = Field(default=None, max_length=512)


class MaskingColumnResponse(MaskingColumnBase):
    """脱敏字段响应"""

    id: int
    table_id: int

    model_config = ConfigDict(from_attributes=True)


# ==================== 脱敏模板 ====================

class MaskingTemplateBase(BaseModel):
    """脱敏模板基础"""

    template_name: str = Field(..., max_length=128, description="模板名称")
    template_code: Optional[str] = Field(default=None, max_length=64, description="模板编码")
    description: Optional[str] = Field(default=None, description="模板描述")
    config_json: Optional[Dict[str, Any]] = Field(default=None, description="模板配置")


class MaskingTemplateCreate(MaskingTemplateBase):
    """创建脱敏模板"""
    pass


class MaskingTemplateResponse(MaskingTemplateBase, TimestampMixin):
    """脱敏模板响应"""

    id: int
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 任务执行 ====================

class MaskingTaskExecutionResponse(BaseModel):
    """脱敏任务执行记录响应"""

    id: int
    task_id: int
    execution_no: str
    trigger_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    total_records: int = 0
    success_records: int = 0
    failed_records: int = 0
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaskingTaskExecuteRequest(BaseModel):
    """脱敏任务执行请求"""

    task_id: int = Field(..., description="任务ID")
    remark: Optional[str] = Field(default=None, description="备注")


# 更新前向引用
MaskingTaskResponse.model_rebuild()
MaskingTableResponse.model_rebuild()
