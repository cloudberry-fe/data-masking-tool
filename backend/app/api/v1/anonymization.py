"""
原地匿名化 API

原地匿名化特点:
- 永久修改原表数据
- 不可逆操作
- 适用于 GDPR 合规、数据销毁场景
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


# ==================== 请求模型 ====================

class CreateAnonymizationTaskRequest(BaseModel):
    """创建匿名化任务请求"""
    task_name: str = Field(..., description="任务名称")
    datasource_id: int = Field(..., description="数据源ID")
    schema_name: str = Field(default="public", description="Schema名")
    table_name: str = Field(..., description="要匿名化的表名")
    backup_before_anonymize: bool = Field(default=True, description="执行前是否备份")
    description: Optional[str] = Field(default=None, description="描述")


class AddAnonymizationColumnRequest(BaseModel):
    """添加匿名化字段规则请求"""
    column_name: str = Field(..., description="字段名")
    masking_algorithm: str = Field(..., description="脱敏算法")
    algorithm_params: Optional[Dict[str, Any]] = Field(default=None, description="算法参数")


# ==================== API 端点 ====================

@router.get("/tasks", response_model=Response[PageResponse])
def get_anonymization_tasks(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    datasource_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """
    获取匿名化任务列表

    匿名化任务特点：
    - 永久修改原表数据
    - 不可逆操作
    - 可选执行前备份
    """
    from app.models.dynamic_masking import AnonymizationTask

    query = db.query(AnonymizationTask)

    if datasource_id:
        query = query.filter(AnonymizationTask.datasource_id == datasource_id)
    if status:
        query = query.filter(AnonymizationTask.status == status)

    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    return Response(data=PageResponse(
        items=[{
            "id": t.id,
            "taskName": t.task_name,
            "datasourceId": t.datasource_id,
            "schemaName": t.schema_name,
            "tableName": t.table_name,
            "backupBeforeAnonymize": t.backup_before_anonymize,
            "status": t.status,
            "lastExecutedAt": t.last_executed_at.isoformat() if t.last_executed_at else None,
            "createdAt": t.created_at.isoformat() if t.created_at else None,
        } for t in tasks],
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("/tasks", response_model=Response)
def create_anonymization_task(
    request: CreateAnonymizationTaskRequest,
    db: DBSession = None,
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """
    创建匿名化任务

    参数:
    - task_name: 任务名称
    - datasource_id: 数据源ID
    - schema_name: Schema名
    - table_name: 要匿名化的表名
    - backup_before_anonymize: 执行前是否备份（强烈建议）
    """
    from app.models.dynamic_masking import AnonymizationTask

    task = AnonymizationTask(
        task_name=request.task_name,
        datasource_id=request.datasource_id,
        schema_name=request.schema_name or "public",
        table_name=request.table_name,
        backup_before_anonymize=request.backup_before_anonymize,
        backup_table_name=f"{request.table_name}_backup_{__import__('datetime').datetime.now().strftime('%Y%m%d')}" if request.backup_before_anonymize else None,
        description=request.description,
        created_by=current_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    audit("CREATE", "anonymization", f"创建匿名化任务: {request.task_name}")

    return Response(data={
        "id": task.id,
        "taskName": task.task_name,
        "message": "创建成功，请配置字段匿名化规则"
    })


@router.post("/tasks/{task_id}/columns", response_model=Response)
def add_column_rule(
    task_id: int,
    request: AddAnonymizationColumnRequest,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    为匿名化任务添加字段配置

    参数:
    - task_id: 任务ID
    - column_name: 字段名
    - masking_algorithm: 脱敏算法
    - algorithm_params: 算法参数
    """
    from app.models.dynamic_masking import AnonymizationTask, AnonymizationColumnRule

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    column_rule = AnonymizationColumnRule(
        task_id=task_id,
        column_name=request.column_name,
        masking_algorithm=request.masking_algorithm,
        algorithm_params=request.algorithm_params or {},
    )

    db.add(column_rule)
    db.commit()

    return Response(message=f"字段 {request.column_name} 匿名化规则添加成功")


@router.post("/tasks/{task_id}/execute", response_model=Response)
def execute_anonymization(
    task_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """
    执行匿名化任务

    ⚠️ 警告: 此操作将永久修改原表数据！

    执行步骤:
    1. 可选：创建备份表
    2. UPDATE 原表数据
    3. 记录执行日志
    """
    from app.models.dynamic_masking import AnonymizationTask, AnonymizationExecution
    from app.models.datasource import DataSource
    from app.services.datasource_service import DataSourceService
    from app.utils.hashdata_anon import HashDataAnonManager, MaskingColumnConfig, MaskingTableConfig
    import datetime

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not task.column_rules:
        raise HTTPException(status_code=400, detail="请先配置字段匿名化规则")

    datasource = db.get(DataSource, task.datasource_id)
    datasource_config = DataSourceService.get_datasource_config(datasource)

    # 创建执行记录
    execution = AnonymizationExecution(
        task_id=task_id,
        execution_no=f"ANON{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{task_id:03d}",
        status="RUNNING",
        start_time=datetime.datetime.now(),
    )
    db.add(execution)
    db.commit()

    anon_manager = HashDataAnonManager(datasource_config)

    try:
        # 构建配置
        column_configs = [
            MaskingColumnConfig(
                column_name=col.column_name,
                algorithm=col.masking_algorithm,
                params=col.algorithm_params or {},
            )
            for col in task.column_rules
        ]

        table_config = MaskingTableConfig(
            source_table=f"{task.schema_name}.{task.table_name}",
            target_table="",  # 匿名化不需要目标表
            columns=column_configs,
        )

        # 生成 SQL
        sql = anon_manager.generate_anonymize_sql(
            table_config,
            source_schema=task.schema_name,
        )

        # 如果需要备份，添加备份语句
        if task.backup_before_anonymize and task.backup_table_name:
            backup_sql = f"CREATE TABLE {task.schema_name}.{task.backup_table_name} AS SELECT * FROM {task.schema_name}.{task.table_name};\n"
            sql = backup_sql + sql

        # 执行
        import psycopg2
        conn = anon_manager._get_connection(datasource_config)
        cursor = conn.cursor()

        for statement in sql.split(";"):
            lines = statement.strip().split('\n')
            actual_sql = ' '.join(line.strip() for line in lines
                                  if line.strip() and not line.strip().startswith("--"))
            if actual_sql:
                cursor.execute(actual_sql)

        # 获取处理行数
        cursor.execute(f"SELECT count(*) FROM {task.schema_name}.{task.table_name}")
        rowcount = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        # 更新执行记录
        execution.status = "SUCCESS"
        execution.end_time = datetime.datetime.now()
        execution.total_records = rowcount
        db.commit()

        # 更新任务状态
        task.last_executed_at = datetime.datetime.now()
        task.status = "EXECUTED"
        db.commit()

        audit("EXECUTE", "anonymization", f"执行匿名化任务: {task.task_name}，处理 {rowcount} 条记录")

        return Response(
            message=f"匿名化完成，永久修改了 {rowcount} 条记录",
            data={
                "executionId": execution.id,
                "executionNo": execution.execution_no,
                "totalRecords": rowcount,
                "backupTable": task.backup_table_name if task.backup_before_anonymize else None,
            }
        )

    except Exception as e:
        execution.status = "FAILED"
        execution.error_message = str(e)
        execution.end_time = datetime.datetime.now()
        db.commit()

        raise HTTPException(status_code=500, detail=f"匿名化失败: {str(e)}")


@router.get("/tasks/{task_id}/preview-sql", response_model=Response)
def preview_anonymization_sql(
    task_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """预览匿名化 SQL（不执行）"""
    from app.models.dynamic_masking import AnonymizationTask
    from app.models.datasource import DataSource
    from app.services.datasource_service import DataSourceService
    from app.utils.hashdata_anon import HashDataAnonManager, MaskingColumnConfig, MaskingTableConfig

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    datasource = db.get(DataSource, task.datasource_id)
    datasource_config = DataSourceService.get_datasource_config(datasource)

    anon_manager = HashDataAnonManager(datasource_config)

    column_configs = [
        MaskingColumnConfig(
            column_name=col.column_name,
            algorithm=col.masking_algorithm,
            params=col.algorithm_params or {},
        )
        for col in task.column_rules
    ]

    table_config = MaskingTableConfig(
        source_table=f"{task.schema_name}.{task.table_name}",
        target_table="",
        columns=column_configs,
    )

    sql = anon_manager.generate_anonymize_sql(
        table_config,
        source_schema=task.schema_name,
    )

    # 添加备份语句
    if task.backup_before_anonymize and task.backup_table_name:
        backup_sql = f"-- 备份原表\nCREATE TABLE {task.schema_name}.{task.backup_table_name} AS SELECT * FROM {task.schema_name}.{task.table_name};\n\n"
        sql = backup_sql + sql

    return Response(data={
        "sql": sql,
        "tableName": task.table_name,
        "backupTable": task.backup_table_name if task.backup_before_anonymize else None,
        "warning": "⚠️ 此 SQL 将永久修改原表数据，请谨慎执行！",
    })


@router.delete("/tasks/{task_id}", response_model=Response)
def delete_anonymization_task(
    task_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """删除匿名化任务（仅限DRAFT状态）"""
    from app.models.dynamic_masking import AnonymizationTask

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "EXECUTED":
        raise HTTPException(status_code=400, detail="已执行的任务不能删除")

    db.delete(task)
    db.commit()

    audit("DELETE", "anonymization", f"删除匿名化任务: {task.task_name}")

    return Response(message="删除成功")


@router.get("/executions/{execution_id}", response_model=Response)
def get_execution_detail(
    execution_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """获取匿名化执行详情"""
    from app.models.dynamic_masking import AnonymizationExecution

    execution = db.get(AnonymizationExecution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    # 计算执行时长
    duration = None
    if execution.start_time and execution.end_time:
        delta = execution.end_time - execution.start_time
        duration = {
            "seconds": int(delta.total_seconds()),
            "formatted": f"{int(delta.total_seconds() // 60)}m {int(delta.total_seconds() % 60)}s"
        }

    return Response(data={
        "id": execution.id,
        "executionNo": execution.execution_no,
        "status": execution.status,
        "startTime": execution.start_time.isoformat() if execution.start_time else None,
        "endTime": execution.end_time.isoformat() if execution.end_time else None,
        "duration": duration,
        "totalRecords": execution.total_records,
        "errorMessage": execution.error_message,
    })
