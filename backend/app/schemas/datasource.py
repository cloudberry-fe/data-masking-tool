"""
数据源管理相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.schemas.common import TimestampMixin


# 数据源类型常量
DATASOURCE_TYPES = {
    "MPP": "HashData Lightning (MPP)",
    "ORACLE": "Oracle",
    "MYSQL": "MySQL",
    "GOLDENDB": "GoldenDB",
    "DM": "达梦",
}


class DataSourceBase(BaseModel):
    """数据源基础信息"""

    datasource_name: str = Field(..., min_length=1, max_length=128, description="数据源名称")
    datasource_type: str = Field(..., description="数据源类型")
    host: Optional[str] = Field(default=None, max_length=256, description="主机地址")
    port: Optional[int] = Field(default=None, description="端口")
    database_name: Optional[str] = Field(default=None, max_length=128, description="数据库名")
    username: Optional[str] = Field(default=None, max_length=128, description="用户名")
    enable_account_mapping: bool = Field(default=False, description="是否启用账号映射")


class DataSourceCreate(DataSourceBase):
    """创建数据源"""

    password: Optional[str] = Field(default=None, description="密码")
    config_json: Optional[Dict[str, Any]] = Field(default=None, description="扩展配置")


class DataSourceUpdate(BaseModel):
    """更新数据源"""

    datasource_name: Optional[str] = Field(default=None, max_length=128)
    host: Optional[str] = Field(default=None, max_length=256)
    port: Optional[int] = None
    database_name: Optional[str] = Field(default=None, max_length=128)
    username: Optional[str] = Field(default=None, max_length=128)
    password: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    enable_account_mapping: Optional[bool] = None
    status: Optional[int] = None


class DataSourceResponse(DataSourceBase, TimestampMixin):
    """数据源响应"""

    id: int
    status: int
    created_by: Optional[int] = None
    config_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class DataSourceTest(BaseModel):
    """数据源连接测试请求"""

    datasource_type: str = Field(..., description="数据源类型")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    database_name: Optional[str] = None
    username: str = Field(..., description="用户名")
    password: Optional[str] = None


class DataSourceTestResponse(BaseModel):
    """数据源连接测试响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    version: Optional[str] = Field(default=None, description="数据库版本")


class TableInfo(BaseModel):
    """表信息"""

    table_name: str = Field(..., description="表名")
    table_comment: Optional[str] = Field(default=None, description="表注释")


class ColumnInfo(BaseModel):
    """字段信息"""

    column_name: str = Field(..., description="字段名")
    data_type: str = Field(..., description="数据类型")
    column_comment: Optional[str] = Field(default=None, description="字段注释")
    is_nullable: bool = Field(default=True, description="是否可空")


class ReferenceInfo(BaseModel):
    """引用信息"""

    reference_type: str
    reference_id: str
    reference_name: str
    created_at: datetime


# ==================== 账号映射 ====================

class AccountMappingBase(BaseModel):
    """账号映射基础"""

    source_account: str = Field(..., max_length=128, description="源账号")
    target_account: str = Field(..., max_length=128, description="目标账号")


class AccountMappingCreate(AccountMappingBase):
    """创建账号映射"""
    pass


class AccountMappingResponse(AccountMappingBase):
    """账号映射响应"""

    id: int
    datasource_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
