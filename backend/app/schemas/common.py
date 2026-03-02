"""
通用Schema定义
"""
from typing import Generic, List, Optional, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """通用响应"""

    code: int = Field(default=0, description="响应码，0表示成功")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": 0,
            "message": "success",
            "data": None
        }
    })


class PageResponse(BaseModel, Generic[T]):
    """分页响应"""

    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页数量")


class PageQuery(BaseModel):
    """分页查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(default=None, description="搜索关键词")


class IdList(BaseModel):
    """ID列表"""

    ids: List[int] = Field(description="ID列表")


class Option(BaseModel):
    """选项"""

    label: str = Field(description="显示标签")
    value: Any = Field(description="选项值")


class TimestampMixin(BaseModel):
    """时间戳混入"""

    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
