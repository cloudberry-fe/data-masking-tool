"""
数据脱敏API
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.schemas.masking import (
    MaskingTaskResponse,
    MaskingTaskCreate,
    MaskingTaskUpdate,
    MaskingTableResponse,
    MaskingTableCreate,
    MaskingTableUpdate,
    MaskingColumnResponse,
    MaskingColumnCreate,
    MaskingColumnUpdate,
    MaskingTemplateResponse,
    MaskingTemplateCreate,
    MaskingTaskExecutionResponse,
    MaskingTaskExecuteRequest,
)
from app.services.masking_service import MaskingService
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


# ==================== 脱敏任务 ====================

@router.get("/tasks", response_model=Response[PageResponse[MaskingTaskResponse]])
def get_tasks(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    datasource_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
):
    """获取脱敏任务列表"""
    tasks, total = MaskingService.get_tasks(
        db, page, page_size, keyword, datasource_id, status
    )
    return Response(data=PageResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("/tasks", response_model=Response[MaskingTaskResponse])
def create_task(
    request: MaskingTaskCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建脱敏任务"""
    task = MaskingService.create_task(
        db,
        task_name=request.task_name,
        datasource_id=request.datasource_id,
        task_code=request.task_code,
        description=request.description,
        source_schema=request.source_schema,
        target_schema=request.target_schema,
        task_type=request.task_type,
        schedule_type=request.schedule_type,
        cron_expression=request.cron_expression,
        created_by=current_user.id,
    )
    audit("CREATE", "masking", f"创建脱敏任务: {request.task_name}")
    return Response(data=task, message="创建成功")


@router.get("/tasks/{task_id}", response_model=Response[MaskingTaskResponse])
def get_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取脱敏任务详情"""
    task = MaskingService.get_task_with_details(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return Response(data=task)


@router.put("/tasks/{task_id}", response_model=Response[MaskingTaskResponse])
def update_task(
    task_id: int,
    request: MaskingTaskUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新脱敏任务"""
    task = MaskingService.update_task(
        db,
        task_id,
        task_name=request.task_name,
        description=request.description,
        source_schema=request.source_schema,
        target_schema=request.target_schema,
        schedule_type=request.schedule_type,
        cron_expression=request.cron_expression,
        status=request.status,
    )
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    audit("UPDATE", "masking", f"更新脱敏任务: {task.task_name}")
    return Response(data=task, message="更新成功")


@router.delete("/tasks/{task_id}", response_model=Response)
def delete_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除脱敏任务"""
    task = MaskingService.get_task(db, task_id)
    if task:
        name = task.task_name
        success = MaskingService.delete_task(db, task_id)
        if success:
            audit("DELETE", "masking", f"删除脱敏任务: {name}")
    return Response(message="删除成功")


@router.post("/tasks/{task_id}/execute", response_model=Response[Dict[str, Any]])
def execute_task(
    task_id: int,
    request: Optional[MaskingTaskExecuteRequest] = None,
    db: DBSession = Depends(get_db),
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """执行脱敏任务"""
    task = MaskingService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 创建执行记录
    execution = MaskingService.create_execution(db, task_id, "MANUAL")
    audit("EXECUTE", "masking", f"执行脱敏任务: {task.task_name}, 执行编号: {execution.execution_no}")

    # 同步执行（实际生产环境应该用Celery异步执行）
    result = MaskingService.execute_masking(db, task_id, execution.id)

    return Response(data=result, message=result.get("message", "任务已提交"))


# ==================== 表配置 ====================

@router.get("/tasks/{task_id}/tables", response_model=Response[List[MaskingTableResponse]])
def get_task_tables(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取任务的表配置列表"""
    task = MaskingService.get_task_with_details(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return Response(data=task.tables)


@router.post("/tasks/{task_id}/tables", response_model=Response[MaskingTableResponse])
def create_table(
    task_id: int,
    request: MaskingTableCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建表配置"""
    table = MaskingService.create_table(
        db,
        task_id=task_id,
        table_name=request.table_name,
        source_table=request.source_table,
        target_table=request.target_table,
        order_no=request.order_no,
        enabled=request.enabled,
    )
    audit("CREATE", "masking", f"添加表配置: {request.table_name}")
    return Response(data=table, message="创建成功")


@router.put("/tables/{table_id}", response_model=Response[MaskingTableResponse])
def update_table(
    table_id: int,
    request: MaskingTableUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新表配置"""
    table = MaskingService.update_table(
        db,
        table_id,
        source_table=request.source_table,
        target_table=request.target_table,
        order_no=request.order_no,
        enabled=request.enabled,
    )
    if not table:
        raise HTTPException(status_code=404, detail="表配置不存在")
    audit("UPDATE", "masking", f"更新表配置: {table.table_name}")
    return Response(data=table, message="更新成功")


@router.delete("/tables/{table_id}", response_model=Response)
def delete_table(
    table_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除表配置"""
    success = MaskingService.delete_table(db, table_id)
    if success:
        audit("DELETE", "masking", "删除表配置")
    return Response(message="删除成功")


# ==================== 字段配置 ====================

@router.get("/tables/{table_id}/columns", response_model=Response[List[MaskingColumnResponse]])
def get_table_columns(
    table_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取表的字段配置列表"""
    table = db.execute(
        "SELECT * FROM masking_table WHERE id = :table_id",
        {"table_id": table_id}
    ).first()
    if not table:
        raise HTTPException(status_code=404, detail="表配置不存在")

    from sqlalchemy import select
    from app.models.masking import MaskingColumn
    columns = db.scalars(select(MaskingColumn).where(MaskingColumn.table_id == table_id)).all()
    return Response(data=columns)


@router.post("/tables/{table_id}/columns", response_model=Response[MaskingColumnResponse])
def create_column(
    table_id: int,
    request: MaskingColumnCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建字段配置"""
    column = MaskingService.create_column(
        db,
        table_id=table_id,
        column_name=request.column_name,
        masking_algorithm=request.masking_algorithm,
        data_type=request.data_type,
        algorithm_params=request.algorithm_params,
        description=request.description,
    )
    audit("CREATE", "masking", f"添加字段配置: {request.column_name}")
    return Response(data=column, message="创建成功")


@router.put("/columns/{column_id}", response_model=Response[MaskingColumnResponse])
def update_column(
    column_id: int,
    request: MaskingColumnUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新字段配置"""
    column = MaskingService.update_column(
        db,
        column_id,
        data_type=request.data_type,
        masking_algorithm=request.masking_algorithm,
        algorithm_params=request.algorithm_params,
        description=request.description,
    )
    if not column:
        raise HTTPException(status_code=404, detail="字段配置不存在")
    audit("UPDATE", "masking", f"更新字段配置: {column.column_name}")
    return Response(data=column, message="更新成功")


@router.delete("/columns/{column_id}", response_model=Response)
def delete_column(
    column_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除字段配置"""
    success = MaskingService.delete_column(db, column_id)
    if success:
        audit("DELETE", "masking", "删除字段配置")
    return Response(message="删除成功")


# ==================== 执行记录 ====================

@router.get("/tasks/{task_id}/executions", response_model=Response[PageResponse[MaskingTaskExecutionResponse]])
def get_executions(
    task_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
):
    """获取执行历史"""
    executions, total = MaskingService.get_executions(db, task_id, page, page_size)
    return Response(data=PageResponse(
        items=executions,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.get("/executions/{execution_id}", response_model=Response[MaskingTaskExecutionResponse])
def get_execution(
    execution_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取执行详情"""
    execution = MaskingService.get_execution(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return Response(data=execution)


# ==================== 脱敏算法 ====================

@router.get("/algorithms")
def get_algorithms():
    """获取脱敏算法列表"""
    algorithms = MaskingService.get_algorithms()
    return Response(data=algorithms)


# ==================== 脱敏模板 ====================

@router.get("/templates", response_model=Response[PageResponse[MaskingTemplateResponse]])
def get_templates(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
):
    """获取脱敏模板列表"""
    templates, total = MaskingService.get_templates(db, page, page_size, keyword)
    return Response(data=PageResponse(
        items=templates,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("/templates", response_model=Response[MaskingTemplateResponse])
def create_template(
    request: MaskingTemplateCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建脱敏模板"""
    template = MaskingService.create_template(
        db,
        template_name=request.template_name,
        template_code=request.template_code,
        description=request.description,
        config_json=request.config_json,
        created_by=current_user.id,
    )
    audit("CREATE", "masking", f"创建脱敏模板: {request.template_name}")
    return Response(data=template, message="创建成功")


@router.delete("/templates/{template_id}", response_model=Response)
def delete_template(
    template_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除脱敏模板"""
    success = MaskingService.delete_template(db, template_id)
    if success:
        audit("DELETE", "masking", "删除脱敏模板")
    return Response(message="删除成功")
