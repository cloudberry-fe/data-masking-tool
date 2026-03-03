"""
翻数工具API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.schemas.sync import (
    DataSyncTaskResponse,
    DataSyncTaskCreate,
    DataSyncTaskUpdate,
)
from app.models.sync import DataSyncTask
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


@router.get("/tasks", response_model=Response[PageResponse[DataSyncTaskResponse]])
def get_tasks(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
):
    """获取翻数任务列表"""
    from sqlalchemy import select, func

    query = select(DataSyncTask)

    if keyword:
        query = query.where(DataSyncTask.task_name.contains(keyword))
    if status:
        query = query.where(DataSyncTask.status == status)

    # 查询总数
    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt)

    # 分页查询
    offset = (page - 1) * page_size
    query = query.order_by(DataSyncTask.created_at.desc()).offset(offset).limit(page_size)
    tasks = db.scalars(query).all()

    return Response(data=PageResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("/tasks", response_model=Response[DataSyncTaskResponse])
def create_task(
    request: DataSyncTaskCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建翻数任务"""
    task = DataSyncTask(
        task_name=request.task_name,
        source_datasource_id=request.source_datasource_id,
        target_datasource_id=request.target_datasource_id,
        sync_mode=request.sync_mode,
        table_mapping=[m.model_dump() for m in request.table_mapping] if request.table_mapping else None,
        schedule_type=request.schedule_type,
        cron_expression=request.cron_expression,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    audit("CREATE", "sync", f"创建翻数任务: {request.task_name}")
    return Response(data=task, message="创建成功")


@router.get("/tasks/{task_id}", response_model=Response[DataSyncTaskResponse])
def get_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取翻数任务详情"""
    from sqlalchemy import select
    task = db.scalar(select(DataSyncTask).where(DataSyncTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return Response(data=task)


@router.put("/tasks/{task_id}", response_model=Response[DataSyncTaskResponse])
def update_task(
    task_id: int,
    request: DataSyncTaskUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新翻数任务"""
    from sqlalchemy import select
    task = db.scalar(select(DataSyncTask).where(DataSyncTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if request.task_name is not None:
        task.task_name = request.task_name
    if request.sync_mode is not None:
        task.sync_mode = request.sync_mode
    if request.table_mapping is not None:
        task.table_mapping = [m.model_dump() for m in request.table_mapping]
    if request.schedule_type is not None:
        task.schedule_type = request.schedule_type
    if request.cron_expression is not None:
        task.cron_expression = request.cron_expression
    if request.status is not None:
        task.status = request.status

    db.add(task)
    db.commit()
    db.refresh(task)

    audit("UPDATE", "sync", f"更新翻数任务: {task.task_name}")
    return Response(data=task, message="更新成功")


@router.delete("/tasks/{task_id}", response_model=Response)
def delete_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除翻数任务"""
    from sqlalchemy import select
    task = db.scalar(select(DataSyncTask).where(DataSyncTask.id == task_id))
    if task:
        name = task.task_name
        db.delete(task)
        db.commit()
        audit("DELETE", "sync", f"删除翻数任务: {name}")
    return Response(message="删除成功")


@router.post("/tasks/{task_id}/execute", response_model=Response)
def execute_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """执行翻数任务"""
    from sqlalchemy import select
    task = db.scalar(select(DataSyncTask).where(DataSyncTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    audit("EXECUTE", "sync", f"执行翻数任务: {task.task_name}")
    return Response(message="任务已提交执行（演示版本）")
