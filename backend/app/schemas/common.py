"""
Common Schema Definitions
"""
from typing import Generic, List, Optional, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """Generic response"""

    code: int = Field(default=0, description="Response code, 0 indicates success")
    message: str = Field(default="success", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 0,
                "message": "success",
                "data": None
            }
        },
        populate_by_name=True
    )


class PageResponse(BaseModel, Generic[T]):
    """Paginated response"""

    items: List[T] = Field(description="Data list")
    total: int = Field(description="Total count")
    page: int = Field(description="Current page")
    page_size: int = Field(
        description="Items per page",
        serialization_alias='pageSize'
    )

    model_config = ConfigDict(populate_by_name=True)


class PageQuery(BaseModel):
    """Paginated query parameters"""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page",
        validation_alias='pageSize',
        serialization_alias='pageSize'
    )
    keyword: Optional[str] = Field(default=None, description="Search keyword")

    model_config = ConfigDict(populate_by_name=True)


class IdList(BaseModel):
    """ID list"""

    ids: List[int] = Field(description="ID list")


class Option(BaseModel):
    """Option"""

    label: str = Field(description="Display label")
    value: Any = Field(description="Option value")


class TimestampMixin(BaseModel):
    """Timestamp mixin"""

    created_at: Optional[datetime] = Field(
        default=None,
        description="Created time",
        serialization_alias='createdAt'
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Updated time",
        serialization_alias='updatedAt'
    )
