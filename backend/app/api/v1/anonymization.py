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
    task_name: Optional[str] = Field(default=None, description="任务名称 (snake_case)")
    taskName: Optional[str] = Field(default=None, description="任务名称 (camelCase)")
    datasource_id: Optional[int] = Field(default=None, description="数据源ID (snake_case)")
    datasourceId: Optional[int] = Field(default=None, description="数据源ID (camelCase)")
    schema_name: str = Field(default="public", description="Schema名 (snake_case)")
    schemaName: Optional[str] = Field(default=None, description="Schema名 (camelCase)")
    table_name: Optional[str] = Field(default=None, description="要匿名化的表名 (snake_case)")
    tableName: Optional[str] = Field(default=None, description="要匿名化的表名 (camelCase)")
    backup_before_anonymize: Optional[bool] = Field(default=None, description="执行前是否备份 (snake_case)")
    backupBeforeAnonymize: Optional[bool] = Field(default=None, description="执行前是否备份 (camelCase)")
    description: Optional[str] = Field(default=None, description="描述")

    def get_task_name(self) -> str:
        return self.task_name or self.taskName or ""

    def get_datasource_id(self) -> int:
        return self.datasource_id or self.datasourceId

    def get_schema_name(self) -> str:
        return self.schema_name or self.schemaName or "public"

    def get_table_name(self) -> str:
        return self.table_name or self.tableName

    def get_backup_before_anonymize(self) -> bool:
        if self.backup_before_anonymize is not None:
            return self.backup_before_anonymize
        if self.backupBeforeAnonymize is not None:
            return self.backupBeforeAnonymize
        return True


class AddAnonymizationColumnRequest(BaseModel):
    """添加匿名化字段规则请求"""
    column_name: Optional[str] = Field(default=None, description="字段名 (snake_case)")
    columnName: Optional[str] = Field(default=None, description="字段名 (camelCase)")
    masking_algorithm: Optional[str] = Field(default=None, description="脱敏算法 (snake_case)")
    maskingAlgorithm: Optional[str] = Field(default=None, description="脱敏算法 (camelCase)")
    algorithm_params: Optional[Dict[str, Any]] = Field(default=None, description="算法参数 (snake_case)")
    algorithmParams: Optional[Dict[str, Any]] = Field(default=None, description="算法参数 (camelCase)")

    def get_column_name(self) -> str:
        return self.column_name or self.columnName

    def get_masking_algorithm(self) -> str:
        return self.masking_algorithm or self.maskingAlgorithm

    def get_algorithm_params(self) -> Dict[str, Any]:
        return self.algorithm_params or self.algorithmParams or {}


class UpdateAnonymizationTaskRequest(BaseModel):
    """更新匿名化任务请求"""
    task_name: Optional[str] = Field(default=None, description="任务名称")
    taskName: Optional[str] = Field(default=None, description="任务名称 (camelCase)")
    schema_name: Optional[str] = Field(default=None, description="Schema名")
    schemaName: Optional[str] = Field(default=None, description="Schema名 (camelCase)")
    table_name: Optional[str] = Field(default=None, description="表名")
    tableName: Optional[str] = Field(default=None, description="表名 (camelCase)")
    backup_before_anonymize: Optional[bool] = Field(default=None, description="执行前是否备份")
    backupBeforeAnonymize: Optional[bool] = Field(default=None, description="执行前是否备份 (camelCase)")
    description: Optional[str] = Field(default=None, description="描述")


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
            "backupTableName": t.backup_table_name,
            "status": t.status,
            "lastExecutedAt": t.last_executed_at.isoformat() if t.last_executed_at else None,
            "createdAt": t.created_at.isoformat() if t.created_at else None,
            "description": t.description,
        } for t in tasks],
        total=total,
        page=page,
        page_size=page_size
    ))


@router.get("/tasks/{task_id}", response_model=Response)
def get_anonymization_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取匿名化任务详情"""
    from app.models.dynamic_masking import AnonymizationTask

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return Response(data={
        "id": task.id,
        "taskName": task.task_name,
        "datasourceId": task.datasource_id,
        "schemaName": task.schema_name,
        "tableName": task.table_name,
        "backupBeforeAnonymize": task.backup_before_anonymize,
        "backupTableName": task.backup_table_name,
        "status": task.status,
        "lastExecutedAt": task.last_executed_at.isoformat() if task.last_executed_at else None,
        "createdAt": task.created_at.isoformat() if task.created_at else None,
        "description": task.description,
        "columnRules": [{
            "id": col.id,
            "columnName": col.column_name,
            "dataType": col.data_type,
            "maskingAlgorithm": col.masking_algorithm,
            "algorithmParams": col.algorithm_params,
        } for col in task.column_rules]
    })


@router.post("/tasks", response_model=Response)
def create_anonymization_task(
    request: CreateAnonymizationTaskRequest,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """
    创建匿名化任务

    参数:
    - taskName: 任务名称
    - datasourceId: 数据源ID
    - schemaName: Schema名
    - tableName: 要匿名化的表名
    - backupBeforeAnonymize: 执行前是否备份（强烈建议）
    """
    from app.models.dynamic_masking import AnonymizationTask
    import datetime

    task_name = request.get_task_name()
    datasource_id = request.get_datasource_id()
    table_name = request.get_table_name()

    if not task_name:
        raise HTTPException(status_code=400, detail="任务名称不能为空")
    if not datasource_id:
        raise HTTPException(status_code=400, detail="数据源ID不能为空")
    if not table_name:
        raise HTTPException(status_code=400, detail="表名不能为空")

    schema_name = request.get_schema_name()
    backup_before = request.get_backup_before_anonymize()

    task = AnonymizationTask(
        task_name=task_name,
        datasource_id=datasource_id,
        schema_name=schema_name,
        table_name=table_name,
        backup_before_anonymize=backup_before,
        backup_table_name=f"{table_name}_backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}" if backup_before else None,
        description=request.description,
        created_by=current_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    audit("CREATE", "anonymization", f"创建匿名化任务: {task_name}")

    return Response(data={
        "id": task.id,
        "taskName": task.task_name,
        "message": "创建成功，请配置字段匿名化规则"
    })


@router.put("/tasks/{task_id}", response_model=Response)
def update_anonymization_task(
    task_id: int,
    request: UpdateAnonymizationTaskRequest,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """
    更新匿名化任务

    只有 DRAFT 状态的任务才能修改
    """
    from app.models.dynamic_masking import AnonymizationTask

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "EXECUTED":
        raise HTTPException(status_code=400, detail="已执行的任务不能修改")

    # 更新字段
    updated = False
    if request.task_name or request.taskName:
        task.task_name = request.task_name or request.taskName
        updated = True
    if request.schema_name or request.schemaName:
        task.schema_name = request.schema_name or request.schemaName
        updated = True
    if request.table_name or request.tableName:
        task.table_name = request.table_name or request.tableName
        # 更新备份表名
        if task.backup_before_anonymize:
            import datetime
            task.backup_table_name = f"{task.table_name}_backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        updated = True
    if request.backup_before_anonymize is not None or request.backupBeforeAnonymize is not None:
        task.backup_before_anonymize = request.backup_before_anonymize if request.backup_before_anonymize is not None else request.backupBeforeAnonymize
        if task.backup_before_anonymize and task.table_name:
            import datetime
            task.backup_table_name = f"{task.table_name}_backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        else:
            task.backup_table_name = None
        updated = True
    if request.description is not None:
        task.description = request.description
        updated = True

    if updated:
        db.commit()
        db.refresh(task)

    audit("UPDATE", "anonymization", f"更新匿名化任务: {task.task_name}")

    return Response(data={
        "id": task.id,
        "taskName": task.task_name,
        "schemaName": task.schema_name,
        "tableName": task.table_name,
        "message": "更新成功"
    })


@router.post("/tasks/{task_id}/columns", response_model=Response)
def add_column_rule(
    task_id: int,
    request: AddAnonymizationColumnRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    为匿名化任务添加字段配置

    参数:
    - task_id: 任务ID
    - columnName: 字段名
    - maskingAlgorithm: 脱敏算法
    - algorithmParams: 算法参数
    """
    from app.models.dynamic_masking import AnonymizationTask, AnonymizationColumnRule

    column_name = request.get_column_name()
    masking_algorithm = request.get_masking_algorithm()

    if not column_name:
        raise HTTPException(status_code=400, detail="字段名不能为空")
    if not masking_algorithm:
        raise HTTPException(status_code=400, detail="脱敏算法不能为空")

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    column_rule = AnonymizationColumnRule(
        task_id=task_id,
        column_name=column_name,
        masking_algorithm=masking_algorithm,
        algorithm_params=request.get_algorithm_params(),
    )

    db.add(column_rule)
    db.commit()

    return Response(message=f"字段 {column_name} 匿名化规则添加成功")


@router.delete("/tasks/{task_id}/columns/{column_id}", response_model=Response)
def delete_column_rule(
    task_id: int,
    column_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """删除字段规则"""
    from app.models.dynamic_masking import AnonymizationColumnRule

    rule = db.get(AnonymizationColumnRule, column_id)
    if not rule or rule.task_id != task_id:
        raise HTTPException(status_code=404, detail="字段规则不存在")

    db.delete(rule)
    db.commit()

    return Response(message="删除成功")


@router.post("/tasks/{task_id}/execute", response_model=Response)
def execute_anonymization(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
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
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")

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
    db.refresh(execution)

    try:
        anon_manager = HashDataAnonManager(datasource_config)

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

        # 获取处理前行数
        cursor.execute(f"SELECT count(*) FROM {task.schema_name}.{task.table_name}")
        rowcount = cursor.fetchone()[0]

        for statement in sql.split(";"):
            lines = statement.strip().split('\n')
            actual_sql = ' '.join(line.strip() for line in lines
                                  if line.strip() and not line.strip().startswith("--"))
            if actual_sql:
                cursor.execute(actual_sql)

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
        import traceback
        error_detail = str(e)
        traceback.print_exc()

        execution.status = "FAILED"
        execution.error_message = error_detail
        execution.end_time = datetime.datetime.now()
        db.commit()

        raise HTTPException(status_code=500, detail=f"匿名化失败: {error_detail}")


@router.get("/tasks/{task_id}/preview-sql", response_model=Response)
def preview_anonymization_sql(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
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

    if task.column_rules:
        column_configs = [
            MaskingColumnConfig(
                column_name=col.column_name,
                algorithm=col.masking_algorithm,
                params=col.algorithm_params or {},
            )
            for col in task.column_rules
        ]
    else:
        column_configs = []

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
        "columnRules": [{"columnName": col.column_name, "maskingAlgorithm": col.masking_algorithm} for col in task.column_rules],
        "warning": "⚠️ 此 SQL 将永久修改原表数据，请谨慎执行！",
    })


@router.delete("/tasks/{task_id}", response_model=Response)
def delete_anonymization_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除匿名化任务（仅限DRAFT状态）"""
    from app.models.dynamic_masking import AnonymizationTask

    task = db.get(AnonymizationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "EXECUTED":
        raise HTTPException(status_code=400, detail="已执行的任务不能删除")

    task_name = task.task_name
    db.delete(task)
    db.commit()

    audit("DELETE", "anonymization", f"删除匿名化任务: {task_name}")

    return Response(message="删除成功")


@router.get("/tasks/{task_id}/executions", response_model=Response[PageResponse])
def get_task_executions(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
):
    """获取任务的执行历史列表"""
    from app.models.dynamic_masking import AnonymizationExecution

    query = db.query(AnonymizationExecution).filter(AnonymizationExecution.task_id == task_id)

    total = query.count()
    executions = query.order_by(AnonymizationExecution.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for e in executions:
        duration = None
        if e.start_time and e.end_time:
            delta = e.end_time - e.start_time
            duration = {
                "seconds": int(delta.total_seconds()),
                "formatted": f"{int(delta.total_seconds() // 60)}m {int(delta.total_seconds() % 60)}s"
            }

        items.append({
            "id": e.id,
            "executionNo": e.execution_no,
            "status": e.status,
            "startTime": e.start_time.isoformat() if e.start_time else None,
            "endTime": e.end_time.isoformat() if e.end_time else None,
            "duration": duration,
            "totalRecords": e.total_records,
            "errorMessage": e.error_message,
            "createdAt": e.created_at.isoformat() if e.created_at else None,
        })

    return Response(data=PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.get("/executions", response_model=Response[PageResponse])
def get_all_executions(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
):
    """获取所有执行历史"""
    from app.models.dynamic_masking import AnonymizationExecution, AnonymizationTask

    query = db.query(AnonymizationExecution)

    if status:
        query = query.filter(AnonymizationExecution.status == status)

    total = query.count()
    executions = query.order_by(AnonymizationExecution.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for e in executions:
        task = db.get(AnonymizationTask, e.task_id)
        duration = None
        if e.start_time and e.end_time:
            delta = e.end_time - e.start_time
            duration = {
                "seconds": int(delta.total_seconds()),
                "formatted": f"{int(delta.total_seconds() // 60)}m {int(delta.total_seconds() % 60)}s"
            }

        items.append({
            "id": e.id,
            "taskId": e.task_id,
            "taskName": task.task_name if task else None,
            "executionNo": e.execution_no,
            "status": e.status,
            "startTime": e.start_time.isoformat() if e.start_time else None,
            "endTime": e.end_time.isoformat() if e.end_time else None,
            "duration": duration,
            "totalRecords": e.total_records,
            "errorMessage": e.error_message,
            "createdAt": e.created_at.isoformat() if e.created_at else None,
        })

    return Response(data=PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.get("/executions/{execution_id}", response_model=Response)
def get_execution_detail(
    execution_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取匿名化执行详情"""
    from app.models.dynamic_masking import AnonymizationExecution, AnonymizationTask

    execution = db.get(AnonymizationExecution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    task = db.get(AnonymizationTask, execution.task_id)

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
        "taskId": execution.task_id,
        "taskName": task.task_name if task else None,
        "executionNo": execution.execution_no,
        "status": execution.status,
        "startTime": execution.start_time.isoformat() if execution.start_time else None,
        "endTime": execution.end_time.isoformat() if execution.end_time else None,
        "duration": duration,
        "totalRecords": execution.total_records,
        "errorMessage": execution.error_message,
        "createdAt": execution.created_at.isoformat() if execution.created_at else None,
    })
