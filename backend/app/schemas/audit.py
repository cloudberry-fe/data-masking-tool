"""
审计日志相关Schema
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class AuditLogResponse(BaseModel):
    """审计日志响应"""

    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    operation_type: Optional[str] = None
    operation_module: Optional[str] = None
    operation_desc: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    response_result: Optional[str] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
