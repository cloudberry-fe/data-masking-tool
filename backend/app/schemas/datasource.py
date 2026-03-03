"""
数据源管理相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, AliasPath
from datetime import datetime
from app.schemas.common import TimestampMixin


# 数据源类型常量
DATASOURCE_TYPES = {
    "MPP": "HashData Lightning (MPP)",
    "ORACLE": "Oracle",
    "MYSQL": "MySQL",
    "GOLDENDB": "GoldenDB",
    "DM": "达梦",
    "POSTGRESQL": "PostgreSQL",
}


class DataSourceBase(BaseModel):
    """数据源基础信息"""

    datasource_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="数据源名称",
        validation_alias=AliasChoices('datasource_name', 'datasourceName'),
        serialization_alias='datasourceName'
    )
    datasource_type: str = Field(
        ...,
        description="数据源类型",
        validation_alias=AliasChoices('datasource_type', 'datasourceType'),
        serialization_alias='datasourceType'
    )
    host: Optional[str] = Field(default=None, max_length=256, description="主机地址")
    port: Optional[int] = Field(default=None, description="端口")
    database_name: Optional[str] = Field(
        default=None,
        max_length=128,
        description="数据库名",
        validation_alias=AliasChoices('database_name', 'databaseName'),
        serialization_alias='databaseName'
    )
    username: Optional[str] = Field(default=None, max_length=128, description="用户名")
    enable_account_mapping: bool = Field(
        default=False,
        description="是否启用账号映射",
        validation_alias=AliasChoices('enable_account_mapping', 'enableAccountMapping'),
        serialization_alias='enableAccountMapping'
    )


class DataSourceCreate(DataSourceBase):
    """创建数据源"""

    password: Optional[str] = Field(default=None, description="密码")
    config_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="扩展配置",
        serialization_alias='configJson'
    )


class DataSourceUpdate(BaseModel):
    """更新数据源"""

    datasource_name: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('datasource_name', 'datasourceName'),
        serialization_alias='datasourceName'
    )
    host: Optional[str] = Field(default=None, max_length=256)
    port: Optional[int] = None
    database_name: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('database_name', 'databaseName'),
        serialization_alias='databaseName'
    )
    username: Optional[str] = Field(default=None, max_length=128)
    password: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = Field(
        default=None,
        serialization_alias='configJson'
    )
    enable_account_mapping: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices('enable_account_mapping', 'enableAccountMapping'),
        serialization_alias='enableAccountMapping'
    )
    status: Optional[int] = None


class DataSourceResponse(DataSourceBase, TimestampMixin):
    """数据源响应"""

    id: int
    status: int
    created_by: Optional[int] = Field(
        default=None,
        serialization_alias='createdBy'
    )
    config_json: Optional[Dict[str, Any]] = Field(
        default=None,
        serialization_alias='configJson'
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DataSourceTest(BaseModel):
    """数据源连接测试请求"""

    datasource_type: str = Field(
        ...,
        description="数据源类型",
        validation_alias=AliasChoices('datasource_type', 'datasourceType'),
        serialization_alias='datasourceType'
    )
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    database_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('database_name', 'databaseName'),
        serialization_alias='databaseName'
    )
    username: str = Field(..., description="用户名")
    password: Optional[str] = None


class DataSourceTestResponse(BaseModel):
    """数据源连接测试响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    version: Optional[str] = Field(default=None, description="数据库版本")


class TableInfo(BaseModel):
    """表信息"""

    table_name: str = Field(
        ...,
        description="表名",
        serialization_alias='tableName'
    )
    table_comment: Optional[str] = Field(
        default=None,
        description="表注释",
        serialization_alias='tableComment'
    )

    model_config = ConfigDict(populate_by_name=True)


class ColumnInfo(BaseModel):
    """字段信息"""

    column_name: str = Field(
        ...,
        description="字段名",
        serialization_alias='columnName'
    )
    data_type: str = Field(
        ...,
        description="数据类型",
        serialization_alias='dataType'
    )
    column_comment: Optional[str] = Field(
        default=None,
        description="字段注释",
        serialization_alias='columnComment'
    )
    is_nullable: bool = Field(
        default=True,
        description="是否可空",
        serialization_alias='isNullable'
    )

    model_config = ConfigDict(populate_by_name=True)


class ReferenceInfo(BaseModel):
    """引用信息"""

    reference_type: str = Field(serialization_alias='referenceType')
    reference_id: str = Field(serialization_alias='referenceId')
    reference_name: str = Field(serialization_alias='referenceName')
    created_at: datetime = Field(serialization_alias='createdAt')

    model_config = ConfigDict(populate_by_name=True)


# ==================== 账号映射 ====================

class AccountMappingBase(BaseModel):
    """账号映射基础"""

    source_account: str = Field(
        ...,
        max_length=128,
        description="源账号",
        serialization_alias='sourceAccount'
    )
    target_account: str = Field(
        ...,
        max_length=128,
        description="目标账号",
        serialization_alias='targetAccount'
    )


class AccountMappingCreate(AccountMappingBase):
    """创建账号映射"""
    pass


class AccountMappingResponse(AccountMappingBase):
    """账号映射响应"""

    id: int
    datasource_id: int = Field(serialization_alias='datasourceId')
    created_at: datetime = Field(serialization_alias='createdAt')

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
