"""
测试数据生成API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import logging

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.schemas.test_data import (
    TestDataTaskCreate,
    TestDataTaskUpdate,
    TestDataTaskResponse,
    TestDataExecutionResponse,
    AnalyzeResult,
    PreviewData,
)
from app.models.test_data import TestDataTask, TestDataExecution
from app.services.test_data_service import get_test_data_service
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tasks", response_model=Response[PageResponse[TestDataTaskResponse]])
def get_tasks(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
):
    """获取测试数据生成任务列表"""
    query = select(TestDataTask)

    if keyword:
        query = query.where(TestDataTask.task_name.contains(keyword))
    if status:
        query = query.where(TestDataTask.status == status)

    # 查询总数
    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt)

    # 分页查询
    offset = (page - 1) * page_size
    query = query.order_by(TestDataTask.created_at.desc()).offset(offset).limit(page_size)
    tasks = db.scalars(query).all()

    return Response(data=PageResponse(
        items=[TestDataTaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("/tasks", response_model=Response[TestDataTaskResponse])
def create_task(
    request: TestDataTaskCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建测试数据生成任务"""
    task_name = request.get_task_name()
    source_datasource_id = request.get_source_datasource_id()
    target_datasource_id = request.get_target_datasource_id()

    if not task_name:
        raise HTTPException(status_code=400, detail="任务名称不能为空")
    if not source_datasource_id:
        raise HTTPException(status_code=400, detail="源数据源ID不能为空")
    if not target_datasource_id:
        raise HTTPException(status_code=400, detail="目标数据源ID不能为空")

    task = TestDataTask(
        task_name=task_name,
        source_datasource_id=source_datasource_id,
        target_datasource_id=target_datasource_id,
        data_ratio=request.get_data_ratio(),
        keep_relations=request.get_keep_relations(),
        table_configs=request.get_table_configs().model_dump() if request.get_table_configs() else None,
        schedule_type=request.get_schedule_type(),
        cron_expression=request.get_cron_expression(),
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    audit("CREATE", "test_data", f"创建测试数据生成任务: {task_name}")
    return Response(data=TestDataTaskResponse.model_validate(task), message="创建成功")


@router.get("/tasks/{task_id}", response_model=Response[TestDataTaskResponse])
def get_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取测试数据生成任务详情"""
    task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return Response(data=TestDataTaskResponse.model_validate(task))


@router.put("/tasks/{task_id}", response_model=Response[TestDataTaskResponse])
def update_task(
    task_id: int,
    request: TestDataTaskUpdate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新测试数据生成任务"""
    task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 支持两种命名格式
    if request.task_name is not None:
        task.task_name = request.task_name
    elif request.taskName is not None:
        task.task_name = request.taskName

    # 更新数据源
    if request.source_datasource_id is not None:
        task.source_datasource_id = request.source_datasource_id
    elif request.sourceDatasourceId is not None:
        task.source_datasource_id = request.sourceDatasourceId

    if request.target_datasource_id is not None:
        task.target_datasource_id = request.target_datasource_id
    elif request.targetDatasourceId is not None:
        task.target_datasource_id = request.targetDatasourceId

    if request.data_ratio is not None:
        task.data_ratio = request.data_ratio
    elif request.dataRatio is not None:
        task.data_ratio = request.dataRatio

    if request.keep_relations is not None:
        task.keep_relations = request.keep_relations
    elif request.keepRelations is not None:
        task.keep_relations = request.keepRelations

    if request.table_configs is not None:
        task.table_configs = request.table_configs.model_dump()
    elif request.tableConfigs is not None:
        task.table_configs = request.tableConfigs.model_dump()

    if request.schedule_type is not None:
        task.schedule_type = request.schedule_type
    elif request.scheduleType is not None:
        task.schedule_type = request.scheduleType

    if request.cron_expression is not None:
        task.cron_expression = request.cron_expression
    elif request.cronExpression is not None:
        task.cron_expression = request.cronExpression

    if request.status is not None:
        task.status = request.status

    db.add(task)
    db.commit()
    db.refresh(task)

    audit("UPDATE", "test_data", f"更新测试数据生成任务: {task.task_name}")
    return Response(data=TestDataTaskResponse.model_validate(task), message="更新成功")


@router.delete("/tasks/{task_id}", response_model=Response)
def delete_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除测试数据生成任务"""
    task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
    if task:
        name = task.task_name
        db.delete(task)
        db.commit()
        audit("DELETE", "test_data", f"删除测试数据生成任务: {name}")
    return Response(message="删除成功")


@router.post("/tasks/{task_id}/analyze", response_model=Response[List[AnalyzeResult]])
def analyze_task(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """分析生产数据特征"""
    task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    service = get_test_data_service()
    results = []

    if task.table_configs and task.table_configs.get("tables"):
        for table_config in task.table_configs["tables"]:
            # 支持两种命名格式
            source_table = table_config.get("source_table") or table_config.get("sourceTable")
            source_schema = table_config.get("source_schema") or table_config.get("sourceSchema") or "public"
            if not source_table:
                continue

            # 如果源表名包含 schema，则解析出来
            if "." in source_table:
                parts = source_table.split(".", 1)
                source_schema = parts[0]
                source_table = parts[1]

            try:
                result = service.analyze_table(db, task.source_datasource_id, source_table, source_schema)
                results.append(result)
            except Exception as e:
                logger.error(f"分析表 {source_table} 失败: {e}")
                results.append({
                    "table_name": source_table,
                    "columns": [],
                    "row_count": 0,
                    "error": str(e)
                })

    audit("ANALYZE", "test_data", f"分析数据特征: 任务ID={task_id}")

    return Response(data=results, message="分析完成")


@router.get("/tasks/{task_id}/preview", response_model=Response[dict])
def preview_data(
    task_id: int,
    db: DBSession,
    current_user: CurrentUser,
    rows: int = 10,
):
    """预览生成的数据"""
    task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    service = get_test_data_service()
    try:
        preview = service.generate_preview(db, task_id, rows)
        return Response(data=preview)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/execute", response_model=Response)
def execute_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """执行测试数据生成"""
    task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 创建执行记录
    execution = TestDataExecution(
        task_id=task_id,
        execution_no=f"EXEC-{task_id}-{func.now()}",
        trigger_type="MANUAL",
        status="PENDING",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # 更新任务状态
    task.status = "RUNNING"
    db.commit()

    # 后台执行 - 不传递 db session，后台任务自己创建
    service = get_test_data_service()
    background_tasks.add_task(
        service.execute_generation,
        task_id,
        execution.id
    )

    audit("EXECUTE", "test_data", f"执行测试数据生成任务: {task.task_name}")
    return Response(message="任务已提交执行")


@router.get("/executions", response_model=Response[PageResponse[TestDataExecutionResponse]])
def get_executions(
    db: DBSession,
    current_user: CurrentUser,
    task_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    """获取执行历史"""
    query = select(TestDataExecution)

    if task_id:
        query = query.where(TestDataExecution.task_id == task_id)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt)

    offset = (page - 1) * page_size
    query = query.order_by(TestDataExecution.created_at.desc()).offset(offset).limit(page_size)
    executions = db.scalars(query).all()

    return Response(data=PageResponse(
        items=[TestDataExecutionResponse.model_validate(e) for e in executions],
        total=total,
        page=page,
        page_size=page_size
    ))


@router.get("/executions/{execution_id}", response_model=Response[TestDataExecutionResponse])
def get_execution(
    execution_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取执行详情"""
    execution = db.scalar(select(TestDataExecution).where(TestDataExecution.id == execution_id))
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return Response(data=TestDataExecutionResponse.model_validate(execution))


@router.get("/generators", response_model=Response[dict])
def get_generators(
    current_user: CurrentUser,
):
    """获取支持的生成器类型"""
    from app.services.test_data_service import TestDataService
    return Response(data=TestDataService.GENERATOR_TYPES)
