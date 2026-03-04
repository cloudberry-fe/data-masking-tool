"""
审计日志相关Schema
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class AuditLogResponse(BaseModel):
    """审计日志响应"""

    id: int
    user_id: Optional[int] = Field(default=None, serialization_alias='userId')
    username: Optional[str] = None
    operation_type: Optional[str] = Field(default=None, serialization_alias='operationType')
    operation_module: Optional[str] = Field(default=None, serialization_alias='operationModule')
    operation_desc: Optional[str] = Field(default=None, serialization_alias='operationDesc')
    request_method: Optional[str] = Field(default=None, serialization_alias='requestMethod')
    request_url: Optional[str] = Field(default=None, serialization_alias='requestUrl')
    request_params: Optional[Dict[str, Any]] = Field(default=None, serialization_alias='requestParams')
    response_result: Optional[str] = Field(default=None, serialization_alias='responseResult')
    error_message: Optional[str] = Field(default=None, serialization_alias='errorMessage')
    ip_address: Optional[str] = Field(default=None, serialization_alias='ipAddress')
    user_agent: Optional[str] = Field(default=None, serialization_alias='userAgent')
    created_at: datetime = Field(serialization_alias='createdAt')

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditLogQuery(BaseModel):
    """审计日志查询"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    username: Optional[str] = Field(default=None, description="用户名")
    operation_type: Optional[str] = Field(default=None, description="操作类型")
    operation_module: Optional[str] = Field(default=None, description="操作模块")
    response_result: Optional[str] = Field(default=None, description="响应结果")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
