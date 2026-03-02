"""
数据源管理API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.schemas.datasource import (
    DataSourceResponse,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceTest,
    DataSourceTestResponse,
    TableInfo,
    ColumnInfo,
    AccountMappingCreate,
    AccountMappingResponse,
)
from app.services.datasource_service import DataSourceService
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


@router.get("", response_model=Response[PageResponse[DataSourceResponse]])
def get_datasources(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    datasource_type: Optional[str] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
):
    """获取数据源列表"""
    datasources, total = DataSourceService.get_datasources(
        db, page, page_size, keyword, datasource_type, status
    )
    return Response(data=PageResponse(
        items=datasources,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("", response_model=Response[DataSourceResponse])
def create_datasource(
    request: DataSourceCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建数据源"""
    datasource = DataSourceService.create_datasource(
        db,
        datasource_name=request.datasource_name,
        datasource_type=request.datasource_type,
        host=request.host,
        port=request.port,
        database_name=request.database_name,
        username=request.username,
        password=request.password,
        config_json=request.config_json,
        enable_account_mapping=request.enable_account_mapping,
        created_by=current_user.id,
    )
    audit("CREATE", "datasource", f"创建数据源: {request.datasource_name}")
    return Response(data=datasource, message="创建成功")


@router.get("/{datasource_id}", response_model=Response[DataSourceResponse])
def get_datasource(
    datasource_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取数据源详情"""
    datasource = DataSourceService.get_datasource(db, datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return Response(data=datasource)


@router.put("/{datasource_id}", response_model=Response[DataSourceResponse])
def update_datasource(
    datasource_id: int,
    request: DataSourceUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新数据源"""
    datasource = DataSourceService.update_datasource(
        db,
        datasource_id,
        datasource_name=request.datasource_name,
        host=request.host,
        port=request.port,
        database_name=request.database_name,
        username=request.username,
        password=request.password,
        config_json=request.config_json,
        enable_account_mapping=request.enable_account_mapping,
        status=request.status,
    )
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    audit("UPDATE", "datasource", f"更新数据源: {datasource.datasource_name}")
    return Response(data=datasource, message="更新成功")


@router.delete("/{datasource_id}", response_model=Response)
def delete_datasource(
    datasource_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除数据源"""
    datasource = DataSourceService.get_datasource(db, datasource_id)
    if not datasource:
        name = datasource.datasource_name
        success = DataSourceService.delete_datasource(db, datasource_id)
        if success:
            audit("DELETE", "datasource", f"删除数据源: {name}")
    return Response(message="删除成功")


@router.post("/test-connection", response_model=Response[DataSourceTestResponse])
def test_connection(
    request: DataSourceTest,
    current_user: CurrentUser,
):
    """测试数据源连接"""
    success, message, version = DataSourceService.test_connection(
        request.datasource_type,
        request.host,
        request.port,
        request.database_name,
        request.username,
        request.password,
    )
    return Response(data=DataSourceTestResponse(
        success=success,
        message=message,
        version=version
    ))


@router.get("/{datasource_id}/tables", response_model=Response[List[TableInfo]])
def get_tables(
    datasource_id: int,
    schema: Optional[str] = None,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取表列表"""
    try:
        tables = DataSourceService.get_tables(db, datasource_id, schema)
        return Response(data=tables)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{datasource_id}/tables/{table_name}/columns", response_model=Response[List[ColumnInfo]])
def get_columns(
    datasource_id: int,
    table_name: str,
    schema: Optional[str] = None,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取字段列表"""
    try:
        columns = DataSourceService.get_columns(db, datasource_id, table_name, schema)
        return Response(data=columns)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{datasource_id}/references")
def get_references(
    datasource_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取数据源引用详情"""
    references = DataSourceService.get_references(db, datasource_id)
    return Response(data=references)


# ==================== 账号映射 ====================

@router.get("/{datasource_id}/account-mappings", response_model=Response[List[AccountMappingResponse]])
def get_account_mappings(
    datasource_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取账号映射列表"""
    mappings = DataSourceService.get_account_mappings(db, datasource_id)
    return Response(data=mappings)


@router.post("/{datasource_id}/account-mappings", response_model=Response[AccountMappingResponse])
def create_account_mapping(
    datasource_id: int,
    request: AccountMappingCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建账号映射"""
    mapping = DataSourceService.create_account_mapping(
        db, datasource_id, request.source_account, request.target_account
    )
    audit("CREATE", "datasource", f"创建账号映射: {request.source_account} -> {request.target_account}")
    return Response(data=mapping, message="创建成功")


@router.delete("/{datasource_id}/account-mappings/{mapping_id}", response_model=Response)
def delete_account_mapping(
    mapping_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除账号映射"""
    success = DataSourceService.delete_account_mapping(db, mapping_id)
    if success:
        audit("DELETE", "datasource", "删除账号映射")
    return Response(message="删除成功")
