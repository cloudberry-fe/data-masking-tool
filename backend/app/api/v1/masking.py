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
from app.models.datasource import DataSource
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


# ==================== 脱敏任务 ====================

@router.get("/tasks", response_model=Response[PageResponse[MaskingTaskResponse]])
def get_tasks(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    datasource_id: Optional[int] = None,
    status: Optional[str] = None,
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
        masking_mode=request.masking_mode,
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
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
    request: Optional[MaskingTaskExecuteRequest] = None,
):
    """执行脱敏任务"""
    task = MaskingService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 创建执行记录
    execution = MaskingService.create_execution(db, task_id, "MANUAL")

    # 同步执行（实际生产环境应该用Celery异步执行）
    result = MaskingService.execute_masking(db, task_id, execution.id)

    # 记录审计日志，包含执行结果
    if result.get("success"):
        audit("EXECUTE", "masking",
              f"执行脱敏任务: {task.task_name}, 执行编号: {execution.execution_no}, 成功记录: {result.get('success_records', 0)}",
              response_result="SUCCESS")
    else:
        audit("EXECUTE", "masking",
              f"执行脱敏任务: {task.task_name}, 执行编号: {execution.execution_no}",
              response_result="FAILED",
              error_message=result.get("message", "执行失败"))

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
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
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
def get_algorithms(
    category: Optional[str] = None,
):
    """获取脱敏算法列表"""
    from app.utils.hashdata_anon import get_all_algorithms, get_algorithm_categories

    algorithms = get_all_algorithms()
    categories = get_algorithm_categories()

    if category:
        algorithms = [a for a in algorithms if a["category"] == category.upper()]

    return Response(data={
        "categories": categories,
        "algorithms": algorithms
    })


@router.get("/algorithms/categories")
def get_algorithm_categories():
    """获取脱敏算法分类"""
    from app.utils.hashdata_anon import get_algorithm_categories
    return Response(data=get_algorithm_categories())


@router.get("/masking-modes")
def get_masking_modes():
    """
    获取脱敏模式列表

    返回所有支持的脱敏模式及其说明：
    - STATIC: 静态脱敏 - 创建脱敏后的数据副本
    - DYNAMIC: 动态脱敏 - 基于角色的查询时脱敏
    - ANONYMIZE: 原地匿名化 - 永久修改原表数据
    - GENERALIZE: 泛化脱敏 - 将精确值转换为范围
    """
    from app.utils.hashdata_anon import MASKING_MODE_DESCRIPTIONS

    modes = []
    for code, info in MASKING_MODE_DESCRIPTIONS.items():
        modes.append({
            "code": code,
            "name": info["name"],
            "description": info["description"],
            "features": info["features"]
        })

    return Response(data=modes)


@router.get("/algorithms/{algorithm_code}")
def get_algorithm_detail(
    algorithm_code: str,
):
    """获取算法详情"""
    from app.utils.hashdata_anon import get_all_algorithms

    algorithms = get_all_algorithms()
    for algo in algorithms:
        if algo["code"].lower() == algorithm_code.lower():
            return Response(data=algo)

    raise HTTPException(status_code=404, detail="算法不存在")


# ==================== 脱敏模板 ====================

@router.get("/templates", response_model=Response[PageResponse[MaskingTemplateResponse]])
def get_templates(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
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


# ==================== SQL 生成 ====================

@router.post("/tasks/{task_id}/generate-sql", response_model=Response[Dict[str, Any]])
def generate_task_sql(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    mode: str = "STATIC",
    masked_role: Optional[str] = None,
    exempted_roles: Optional[str] = None,
):
    """
    生成脱敏任务的SQL语句

    Args:
        task_id: 任务ID
        mode: 脱敏模式
            - STATIC: 静态脱敏（默认）- 创建脱敏后的数据副本
            - DYNAMIC: 动态脱敏 - 基于角色的查询时脱敏
            - ANONYMIZE: 原地匿名化 - 永久修改原表数据
            - GENERALIZE: 泛化脱敏 - 将精确值转换为范围
        masked_role: 动态脱敏时被脱敏的数据库角色
        exempted_roles: 动态脱敏时豁免的角色（逗号分隔）
    """
    from app.utils.hashdata_anon import (
        HashDataAnonManager,
        MaskingTableConfig,
        MaskingColumnConfig,
        MASKING_MODE_DESCRIPTIONS,
    )
    from app.services.datasource_service import DataSourceService

    # 验证模式
    mode = mode.upper()
    if mode not in MASKING_MODE_DESCRIPTIONS:
        raise HTTPException(status_code=400, detail=f"不支持的脱敏模式: {mode}")

    task = MaskingService.get_task_with_details(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not task.tables:
        raise HTTPException(status_code=400, detail="任务没有配置表")

    datasource = db.get(DataSource, task.datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

    # 获取数据源配置
    datasource_config = DataSourceService.get_datasource_config(datasource)
    anon_manager = HashDataAnonManager(datasource_config)

    # 生成所有表的SQL
    all_sql_parts = []
    source_schema = task.source_schema or "public"
    target_schema = task.target_schema or "public"

    # 处理动态脱敏参数
    kwargs = {}
    if mode == "DYNAMIC":
        kwargs["masked_role"] = masked_role or "masked"
        if exempted_roles:
            kwargs["exempted_roles"] = [r.strip() for r in exempted_roles.split(",")]

    for table_config in task.tables:
        if not table_config.enabled or not table_config.columns:
            continue

        # 构建字段配置
        masking_columns = [
            MaskingColumnConfig(
                column_name=col.column_name,
                algorithm=col.masking_algorithm,
                params=col.algorithm_params,
            )
            for col in table_config.columns
        ]

        masking_table_config = MaskingTableConfig(
            source_table=table_config.source_table or table_config.table_name,
            target_table=table_config.target_table or f"{table_config.table_name}_masked",
            columns=masking_columns,
        )

        # 根据模式生成SQL
        sql = anon_manager.generate_masking_sql_by_mode(
            masking_table_config,
            mode=mode,
            source_schema=source_schema,
            target_schema=target_schema,
            **kwargs
        )
        all_sql_parts.append(sql)

    if not all_sql_parts:
        raise HTTPException(status_code=400, detail="没有可用的表配置")

    combined_sql = "\n\n".join(all_sql_parts)

    # 模式说明
    mode_info = MASKING_MODE_DESCRIPTIONS.get(mode, {})

    return Response(data={
        "sql": combined_sql,
        "tableCount": len(all_sql_parts),
        "sourceSchema": source_schema,
        "targetSchema": target_schema,
        "mode": mode,
        "modeName": mode_info.get("name", mode),
        "modeDescription": mode_info.get("description", ""),
    })


# ==================== 执行详情 ====================

@router.get("/executions/{execution_id}/logs", response_model=Response[Dict[str, Any]])
def get_execution_logs(
    execution_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取执行日志详情"""
    execution = MaskingService.get_execution(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    task = MaskingService.get_task(db, execution.task_id)

    # 计算执行时长
    duration = None
    if execution.start_time and execution.end_time:
        delta = execution.end_time - execution.start_time
        duration = {
            "seconds": int(delta.total_seconds()),
            "formatted": f"{int(delta.total_seconds() // 60)} min {int(delta.total_seconds() % 60)} sec"
        }

    return Response(data={
        "execution": {
            "id": execution.id,
            "executionNo": execution.execution_no,
            "taskId": execution.task_id,
            "taskName": task.task_name if task else None,
            "triggerType": execution.trigger_type,
            "status": execution.status,
            "startTime": execution.start_time.isoformat() if execution.start_time else None,
            "endTime": execution.end_time.isoformat() if execution.end_time else None,
            "duration": duration,
            "totalRecords": execution.total_records,
            "successRecords": execution.success_records,
            "failedRecords": execution.failed_records,
            "errorMessage": execution.error_message,
            "createdAt": execution.created_at.isoformat() if execution.created_at else None,
        }
    })
