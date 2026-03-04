"""
审计日志API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.schemas.audit import AuditLogResponse, AuditLogQuery
from app.services.audit_service import AuditService
from app.api.deps import CurrentUser, DBSession

router = APIRouter()


@router.get("/logs", response_model=Response[PageResponse[AuditLogResponse]], response_model_by_alias=True)
def get_audit_logs(
    db: DBSession,
    current_user: CurrentUser,
    query: AuditLogQuery = Depends(),
):
    """获取审计日志列表"""
    logs, total = AuditService.get_logs(
        db,
        page=query.page,
        page_size=query.page_size,
        username=query.username,
        operation_type=query.operation_type,
        operation_module=query.operation_module,
        response_result=query.response_result,
        start_time=query.start_time,
        end_time=query.end_time,
    )
    return Response(data=PageResponse(
        items=logs,
        total=total,
        page=query.page,
        page_size=query.page_size
    ))


@router.get("/logs/{log_id}", response_model=Response[AuditLogResponse], response_model_by_alias=True)
def get_audit_log(
    log_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取审计日志详情"""
    log = AuditService.get_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    return Response(data=log)
