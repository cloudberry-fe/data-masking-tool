"""
测试数据生成相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.schemas.common import TimestampMixin


# ==================== 列配置 ====================

class ColumnGeneratorConfig(BaseModel):
    """列生成器配置"""

    name: str = Field(..., description="列名")
    generator: str = Field(..., description="生成器类型")
    params: Optional[Dict[str, Any]] = Field(default=None, description="生成器参数")


class TableGeneratorConfig(BaseModel):
    """表生成器配置"""

    source_table: Optional[str] = Field(default=None, description="源表名 (snake_case)")
    sourceTable: Optional[str] = Field(default=None, description="源表名 (camelCase)")
    source_schema: Optional[str] = Field(default=None, description="源Schema (snake_case)")
    sourceSchema: Optional[str] = Field(default=None, description="源Schema (camelCase)")
    target_table: Optional[str] = Field(default=None, description="目标表名 (snake_case)")
    targetTable: Optional[str] = Field(default=None, description="目标表名 (camelCase)")
    target_schema: Optional[str] = Field(default=None, description="目标Schema (snake_case)")
    targetSchema: Optional[str] = Field(default=None, description="目标Schema (camelCase)")
    row_count: Optional[int] = Field(default=None, description="生成行数 (snake_case)")
    rowCount: Optional[int] = Field(default=None, description="生成行数 (camelCase)")
    columns: List[ColumnGeneratorConfig] = Field(default_factory=list, description="列配置")

    def get_source_table(self) -> str:
        return self.source_table or self.sourceTable or ""

    def get_source_schema(self) -> str:
        return self.source_schema or self.sourceSchema or "public"

    def get_target_table(self) -> str:
        return self.target_table or self.targetTable or ""

    def get_target_schema(self) -> str:
        return self.target_schema or self.targetSchema or "public"

    def get_row_count(self) -> int:
        return self.row_count or self.rowCount or 100


class RelationConfig(BaseModel):
    """关联关系配置"""

    source_table: Optional[str] = Field(default=None, description="源表 (snake_case)")
    sourceTable: Optional[str] = Field(default=None, description="源表 (camelCase)")
    source_column: Optional[str] = Field(default=None, description="源列 (snake_case)")
    sourceColumn: Optional[str] = Field(default=None, description="源列 (camelCase)")
    reference_table: Optional[str] = Field(default=None, description="引用表 (snake_case)")
    referenceTable: Optional[str] = Field(default=None, description="引用表 (camelCase)")
    reference_column: Optional[str] = Field(default=None, description="引用列 (snake_case)")
    referenceColumn: Optional[str] = Field(default=None, description="引用列 (camelCase)")


class TableConfigs(BaseModel):
    """表配置"""

    tables: List[TableGeneratorConfig] = Field(default_factory=list, description="表配置列表")
    relations: List[RelationConfig] = Field(default_factory=list, description="关联关系配置")


# ==================== 任务 ====================

class TestDataTaskCreate(BaseModel):
    """创建测试数据任务"""

    task_name: Optional[str] = Field(default=None, min_length=1, max_length=128, description="任务名称 (snake_case)")
    taskName: Optional[str] = Field(default=None, min_length=1, max_length=128, description="任务名称 (camelCase)")
    source_datasource_id: Optional[int] = Field(default=None, description="源数据源ID (snake_case)")
    sourceDatasourceId: Optional[int] = Field(default=None, description="源数据源ID (camelCase)")
    target_datasource_id: Optional[int] = Field(default=None, description="目标数据源ID (snake_case)")
    targetDatasourceId: Optional[int] = Field(default=None, description="目标数据源ID (camelCase)")
    data_ratio: Optional[float] = Field(default=None, ge=0.01, le=10.0, description="数据量比例 (snake_case)")
    dataRatio: Optional[float] = Field(default=None, ge=0.01, le=10.0, description="数据量比例 (camelCase)")
    keep_relations: Optional[bool] = Field(default=None, description="保持关联关系 (snake_case)")
    keepRelations: Optional[bool] = Field(default=None, description="保持关联关系 (camelCase)")
    table_configs: Optional[TableConfigs] = Field(default=None, description="表配置 (snake_case)")
    tableConfigs: Optional[TableConfigs] = Field(default=None, description="表配置 (camelCase)")
    schedule_type: Optional[str] = Field(default=None, description="调度类型 (snake_case)")
    scheduleType: Optional[str] = Field(default=None, description="调度类型 (camelCase)")
    cron_expression: Optional[str] = Field(default=None, max_length=128, description="Cron表达式 (snake_case)")
    cronExpression: Optional[str] = Field(default=None, max_length=128, description="Cron表达式 (camelCase)")

    def get_task_name(self) -> str:
        return self.task_name or self.taskName or ""

    def get_source_datasource_id(self) -> int:
        return self.source_datasource_id or self.sourceDatasourceId

    def get_target_datasource_id(self) -> int:
        return self.target_datasource_id or self.targetDatasourceId

    def get_data_ratio(self) -> float:
        return self.data_ratio or self.dataRatio or 1.0

    def get_keep_relations(self) -> bool:
        if self.keep_relations is not None:
            return self.keep_relations
        if self.keepRelations is not None:
            return self.keepRelations
        return True

    def get_table_configs(self) -> Optional[TableConfigs]:
        return self.table_configs or self.tableConfigs

    def get_schedule_type(self) -> str:
        return self.schedule_type or self.scheduleType or "MANUAL"

    def get_cron_expression(self) -> Optional[str]:
        return self.cron_expression or self.cronExpression


class TestDataTaskUpdate(BaseModel):
    """更新测试数据任务"""

    task_name: Optional[str] = Field(default=None, max_length=128)
    taskName: Optional[str] = Field(default=None, max_length=128)
    source_datasource_id: Optional[int] = Field(default=None, description="源数据源ID (snake_case)")
    sourceDatasourceId: Optional[int] = Field(default=None, description="源数据源ID (camelCase)")
    target_datasource_id: Optional[int] = Field(default=None, description="目标数据源ID (snake_case)")
    targetDatasourceId: Optional[int] = Field(default=None, description="目标数据源ID (camelCase)")
    data_ratio: Optional[float] = Field(default=None, ge=0.01, le=10.0)
    dataRatio: Optional[float] = Field(default=None, ge=0.01, le=10.0)
    keep_relations: Optional[bool] = None
    keepRelations: Optional[bool] = None
    table_configs: Optional[TableConfigs] = None
    tableConfigs: Optional[TableConfigs] = None
    schedule_type: Optional[str] = None
    scheduleType: Optional[str] = None
    cron_expression: Optional[str] = Field(default=None, max_length=128)
    cronExpression: Optional[str] = Field(default=None, max_length=128)
    status: Optional[str] = None


class TestDataTaskBase(BaseModel):
    """测试数据任务基础"""

    task_name: str = Field(..., min_length=1, max_length=128, description="任务名称", serialization_alias="taskName")
    source_datasource_id: int = Field(..., description="源数据源ID（生产数据）", serialization_alias="sourceDatasourceId")
    target_datasource_id: int = Field(..., description="目标数据源ID（测试数据）", serialization_alias="targetDatasourceId")
    data_ratio: float = Field(default=1.0, ge=0.01, le=10.0, description="数据量比例", serialization_alias="dataRatio")
    keep_relations: bool = Field(default=True, description="保持关联关系", serialization_alias="keepRelations")
    table_configs: Optional[TableConfigs] = Field(default=None, description="表配置", serialization_alias="tableConfigs")
    schedule_type: str = Field(default="MANUAL", description="调度类型：MANUAL/CRON", serialization_alias="scheduleType")
    cron_expression: Optional[str] = Field(default=None, max_length=128, description="Cron表达式", serialization_alias="cronExpression")


class TestDataTaskResponse(TestDataTaskBase, TimestampMixin):
    """测试数据任务响应"""

    id: int
    status: str
    created_by: Optional[int] = Field(default=None, serialization_alias="createdBy")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, by_alias=True)


# ==================== 数据特征 ====================

class ColumnProfile(BaseModel):
    """列数据特征"""

    data_type: Optional[str] = None
    null_ratio: float = 0.0
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std_dev: Optional[float] = None
    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None
    avg_length: Optional[float] = None
    unique_ratio: Optional[float] = None
    patterns: Optional[List[Dict[str, Any]]] = None
    quartiles: Optional[List[float]] = None


class TestDataProfileCreate(BaseModel):
    """创建数据特征"""

    task_id: int
    table_name: str
    column_name: str
    data_type: Optional[str] = None
    profile_type: Optional[str] = None
    profile_data: Optional[ColumnProfile] = None
    generator_type: Optional[str] = None
    generator_params: Optional[Dict[str, Any]] = None


class TestDataProfileResponse(TestDataProfileCreate):
    """数据特征响应"""

    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 执行 ====================

class TestDataExecutionResponse(BaseModel):
    """测试数据执行响应"""

    id: int
    task_id: int
    execution_no: Optional[str] = None
    trigger_type: Optional[str] = None
    status: str
    total_tables: int = 0
    completed_tables: int = 0
    total_records: int = 0
    success_records: int = 0
    failed_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 分析结果 ====================

class AnalyzeResult(BaseModel):
    """分析结果"""

    table_name: str
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0


class PreviewData(BaseModel):
    """预览数据"""

    table_name: str
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
