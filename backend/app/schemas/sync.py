"""
翻数工具相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.schemas.common import TimestampMixin


class TableMapping(BaseModel):
    """表映射"""

    source_table: str = Field(..., description="源表")
    target_table: str = Field(..., description="目标表")
    column_mapping: Optional[Dict[str, str]] = Field(default=None, description="字段映射")
    where_condition: Optional[str] = Field(default=None, description="过滤条件")


class DataSyncTaskBase(BaseModel):
    """翻数任务基础"""

    task_name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    source_datasource_id: int = Field(..., description="源数据源ID")
    target_datasource_id: int = Field(..., description="目标数据源ID")
    sync_mode: str = Field(default="FULL", description="同步模式：FULL/INCREMENTAL")
    table_mapping: Optional[List[TableMapping]] = Field(default=None, description="表映射配置")
    schedule_type: str = Field(default="MANUAL", description="调度类型：MANUAL/CRON")
    cron_expression: Optional[str] = Field(default=None, max_length=128, description="Cron表达式")


class DataSyncTaskCreate(DataSyncTaskBase):
    """创建翻数任务"""
    pass


class DataSyncTaskUpdate(BaseModel):
    """更新翻数任务"""

    task_name: Optional[str] = Field(default=None, max_length=128)
    sync_mode: Optional[str] = None
    table_mapping: Optional[List[TableMapping]] = None
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = Field(default=None, max_length=128)
    status: Optional[str] = None


class DataSyncTaskResponse(DataSyncTaskBase, TimestampMixin):
    """翻数任务响应"""

    id: int
    status: str
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
