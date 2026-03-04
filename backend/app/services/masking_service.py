"""
数据脱敏服务
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, and_

from app.models.masking import (
    MaskingTask,
    MaskingTable,
    MaskingColumn,
    MaskingTemplate,
    MaskingTaskExecution,
)
from app.models.datasource import DataSource
from app.utils.hashdata_anon import (
    HashDataAnonManager,
    MaskingTableConfig,
    MaskingColumnConfig,
    PREDEFINED_ALGORITHMS,
)
from app.services.datasource_service import DataSourceService

logger = logging.getLogger(__name__)


class MaskingService:
    """数据脱敏服务"""

    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[MaskingTask]:
        """获取脱敏任务"""
        stmt = select(MaskingTask).where(MaskingTask.id == task_id)
        return db.scalar(stmt)

    @staticmethod
    def get_task_with_details(db: Session, task_id: int) -> Optional[MaskingTask]:
        """获取脱敏任务详情（含表和字段配置）"""
        stmt = (
            select(MaskingTask)
            .options(
                selectinload(MaskingTask.tables)
                .selectinload(MaskingTable.columns)
            )
            .where(MaskingTask.id == task_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def get_tasks(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        datasource_id: Optional[int] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Tuple[List[MaskingTask], int]:
        """获取脱敏任务列表"""
        query = select(MaskingTask)

        if keyword:
            query = query.where(
                MaskingTask.task_name.contains(keyword)
            )
        if datasource_id:
            query = query.where(MaskingTask.datasource_id == datasource_id)
        if status:
            query = query.where(MaskingTask.status == status)
        if created_by:
            query = query.where(MaskingTask.created_by == created_by)

        # 查询总数
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_stmt)

        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(MaskingTask.created_at.desc()).offset(offset).limit(page_size)
        tasks = db.scalars(query).all()

        return tasks, total

    @staticmethod
    def generate_task_code() -> str:
        """生成任务编码"""
        return f"MTK{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    @staticmethod
    def create_task(
        db: Session,
        task_name: str,
        datasource_id: int,
        task_code: Optional[str] = None,
        description: Optional[str] = None,
        source_schema: Optional[str] = None,
        target_schema: Optional[str] = None,
        task_type: str = "TABLE",
        schedule_type: str = "MANUAL",
        cron_expression: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> MaskingTask:
        """创建脱敏任务"""
        task = MaskingTask(
            task_name=task_name,
            task_code=task_code or MaskingService.generate_task_code(),
            description=description,
            datasource_id=datasource_id,
            source_schema=source_schema,
            target_schema=target_schema,
            task_type=task_type,
            schedule_type=schedule_type,
            cron_expression=cron_expression,
            status="DRAFT",
            created_by=created_by,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(
        db: Session,
        task_id: int,
        task_name: Optional[str] = None,
        description: Optional[str] = None,
        source_schema: Optional[str] = None,
        target_schema: Optional[str] = None,
        schedule_type: Optional[str] = None,
        cron_expression: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[MaskingTask]:
        """更新脱敏任务"""
        task = MaskingService.get_task(db, task_id)
        if not task:
            return None

        if task_name is not None:
            task.task_name = task_name
        if description is not None:
            task.description = description
        if source_schema is not None:
            task.source_schema = source_schema
        if target_schema is not None:
            task.target_schema = target_schema
        if schedule_type is not None:
            task.schedule_type = schedule_type
        if cron_expression is not None:
            task.cron_expression = cron_expression
        if status is not None:
            task.status = status

        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """删除脱敏任务"""
        task = MaskingService.get_task(db, task_id)
        if not task:
            return False
        db.delete(task)
        db.commit()
        return True

    # ==================== 表配置 ====================

    @staticmethod
    def get_table(db: Session, table_id: int) -> Optional[MaskingTable]:
        """获取表配置"""
        stmt = select(MaskingTable).where(MaskingTable.id == table_id)
        return db.scalar(stmt)

    @staticmethod
    def create_table(
        db: Session,
        task_id: int,
        table_name: str,
        source_table: Optional[str] = None,
        target_table: Optional[str] = None,
        order_no: int = 0,
        enabled: bool = True,
    ) -> MaskingTable:
        """创建表配置"""
        table = MaskingTable(
            task_id=task_id,
            table_name=table_name,
            source_table=source_table or table_name,
            target_table=target_table or f"{table_name}_masked",
            order_no=order_no,
            enabled=enabled,
        )
        db.add(table)
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def update_table(
        db: Session,
        table_id: int,
        source_table: Optional[str] = None,
        target_table: Optional[str] = None,
        order_no: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[MaskingTable]:
        """更新表配置"""
        table = MaskingService.get_table(db, table_id)
        if not table:
            return None

        if source_table is not None:
            table.source_table = source_table
        if target_table is not None:
            table.target_table = target_table
        if order_no is not None:
            table.order_no = order_no
        if enabled is not None:
            table.enabled = enabled

        db.add(table)
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def delete_table(db: Session, table_id: int) -> bool:
        """删除表配置"""
        table = MaskingService.get_table(db, table_id)
        if not table:
            return False
        db.delete(table)
        db.commit()
        return True

    # ==================== 字段配置 ====================

    @staticmethod
    def get_column(db: Session, column_id: int) -> Optional[MaskingColumn]:
        """获取字段配置"""
        stmt = select(MaskingColumn).where(MaskingColumn.id == column_id)
        return db.scalar(stmt)

    @staticmethod
    def create_column(
        db: Session,
        table_id: int,
        column_name: str,
        masking_algorithm: str,
        data_type: Optional[str] = None,
        algorithm_params: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> MaskingColumn:
        """创建字段配置"""
        column = MaskingColumn(
            table_id=table_id,
            column_name=column_name,
            data_type=data_type,
            masking_algorithm=masking_algorithm,
            algorithm_params=algorithm_params,
            description=description,
        )
        db.add(column)
        db.commit()
        db.refresh(column)
        return column

    @staticmethod
    def update_column(
        db: Session,
        column_id: int,
        data_type: Optional[str] = None,
        masking_algorithm: Optional[str] = None,
        algorithm_params: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> Optional[MaskingColumn]:
        """更新字段配置"""
        column = MaskingService.get_column(db, column_id)
        if not column:
            return None

        if data_type is not None:
            column.data_type = data_type
        if masking_algorithm is not None:
            column.masking_algorithm = masking_algorithm
        if algorithm_params is not None:
            column.algorithm_params = algorithm_params
        if description is not None:
            column.description = description

        db.add(column)
        db.commit()
        db.refresh(column)
        return column

    @staticmethod
    def delete_column(db: Session, column_id: int) -> bool:
        """删除字段配置"""
        column = MaskingService.get_column(db, column_id)
        if not column:
            return False
        db.delete(column)
        db.commit()
        return True

    # ==================== 脱敏模板 ====================

    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[MaskingTemplate]:
        """获取脱敏模板"""
        stmt = select(MaskingTemplate).where(MaskingTemplate.id == template_id)
        return db.scalar(stmt)

    @staticmethod
    def get_templates(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
    ) -> Tuple[List[MaskingTemplate], int]:
        """获取脱敏模板列表"""
        query = select(MaskingTemplate)

        if keyword:
            query = query.where(
                MaskingTemplate.template_name.contains(keyword)
            )

        # 查询总数
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_stmt)

        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(MaskingTemplate.created_at.desc()).offset(offset).limit(page_size)
        templates = db.scalars(query).all()

        return templates, total

    @staticmethod
    def generate_template_code() -> str:
        """生成模板编码"""
        return f"TPL{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    def create_template(
        db: Session,
        template_name: str,
        template_code: Optional[str] = None,
        description: Optional[str] = None,
        config_json: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
    ) -> MaskingTemplate:
        """创建脱敏模板"""
        template = MaskingTemplate(
            template_name=template_name,
            template_code=template_code or MaskingService.generate_template_code(),
            description=description,
            config_json=config_json,
            created_by=created_by,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        """删除脱敏模板"""
        template = MaskingService.get_template(db, template_id)
        if not template:
            return False
        db.delete(template)
        db.commit()
        return True

    # ==================== 任务执行 ====================

    @staticmethod
    def generate_execution_no() -> str:
        """生成执行编号"""
        return f"EXE{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"

    @staticmethod
    def create_execution(
        db: Session,
        task_id: int,
        trigger_type: str = "MANUAL",
    ) -> MaskingTaskExecution:
        """创建执行记录"""
        execution = MaskingTaskExecution(
            task_id=task_id,
            execution_no=MaskingService.generate_execution_no(),
            trigger_type=trigger_type,
            status="PENDING",
            total_records=0,
            success_records=0,
            failed_records=0,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def update_execution_status(
        db: Session,
        execution_id: int,
        status: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        total_records: Optional[int] = None,
        success_records: Optional[int] = None,
        failed_records: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[MaskingTaskExecution]:
        """更新执行记录"""
        stmt = select(MaskingTaskExecution).where(MaskingTaskExecution.id == execution_id)
        execution = db.scalar(stmt)
        if not execution:
            return None

        execution.status = status
        if start_time is not None:
            execution.start_time = start_time
        if end_time is not None:
            execution.end_time = end_time
        if total_records is not None:
            execution.total_records = total_records
        if success_records is not None:
            execution.success_records = success_records
        if failed_records is not None:
            execution.failed_records = failed_records
        if error_message is not None:
            execution.error_message = error_message

        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def get_executions(
        db: Session,
        task_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MaskingTaskExecution], int]:
        """获取执行历史"""
        query = select(MaskingTaskExecution).where(MaskingTaskExecution.task_id == task_id)

        # 查询总数
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_stmt)

        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(MaskingTaskExecution.created_at.desc()).offset(offset).limit(page_size)
        executions = db.scalars(query).all()

        return executions, total

    @staticmethod
    def get_execution(db: Session, execution_id: int) -> Optional[MaskingTaskExecution]:
        """获取执行详情"""
        stmt = select(MaskingTaskExecution).where(MaskingTaskExecution.id == execution_id)
        return db.scalar(stmt)

    # ==================== 脱敏执行 ====================

    @staticmethod
    def execute_masking(db: Session, task_id: int, execution_id: int) -> Dict[str, Any]:
        """
        执行脱敏任务

        这是同步执行版本，实际生产环境应该使用异步任务（Celery）
        """
        from datetime import datetime

        task = MaskingService.get_task_with_details(db, task_id)
        if not task:
            return {"success": False, "message": "任务不存在"}

        datasource = db.get(DataSource, task.datasource_id)
        if not datasource:
            return {"success": False, "message": "数据源不存在"}

        # 更新执行状态为运行中
        MaskingService.update_execution_status(
            db, execution_id, "RUNNING", start_time=datetime.now()
        )

        try:
            # 构建脱敏配置
            datasource_config = DataSourceService.get_datasource_config(datasource)
            anon_manager = HashDataAnonManager(datasource_config)

            total_success = 0
            total_failed = 0
            error_messages = []

            # 逐个表执行脱敏
            for table_config in task.tables:
                if not table_config.enabled:
                    continue

                # 构建表脱敏配置
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

                # 生成并执行SQL
                sql = anon_manager.generate_masking_sql(
                    masking_table_config,
                    source_schema=task.source_schema or "public",
                    target_schema=task.target_schema or "public",
                )

                logger.info(f"生成脱敏SQL:\n{sql}")

                # 实际执行脱敏
                result = anon_manager.execute_masking(
                    masking_table_config,
                    datasource_config,
                    source_schema=task.source_schema or "public",
                    target_schema=task.target_schema or "public",
                )

                if result.get("success"):
                    total_success += result.get("rowcount", 0)
                else:
                    total_failed += 1
                    error_msg = f"表 {table_config.table_name} 脱敏失败: {result.get('error', result.get('message', '未知错误'))}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)

            # 判断整体执行结果
            if total_failed > 0 or total_success == 0:
                # 有失败或没有成功记录，标记为失败
                combined_error = "; ".join(error_messages) if error_messages else "执行未产生有效结果"
                MaskingService.update_execution_status(
                    db,
                    execution_id,
                    "FAILED",
                    end_time=datetime.now(),
                    total_records=total_success,
                    success_records=total_success,
                    failed_records=total_failed,
                    error_message=combined_error,
                )
                return {
                    "success": False,
                    "message": f"脱敏任务执行失败: {combined_error}",
                    "total_records": total_success,
                    "success_records": total_success,
                    "failed_records": total_failed,
                    "error_details": error_messages,
                }

            # 更新执行状态为成功
            MaskingService.update_execution_status(
                db,
                execution_id,
                "SUCCESS",
                end_time=datetime.now(),
                total_records=total_success,
                success_records=total_success,
                failed_records=total_failed,
            )

            return {
                "success": True,
                "message": f"脱敏任务执行成功，共处理 {total_success} 条记录",
                "total_records": total_success,
                "success_records": total_success,
                "failed_records": total_failed,
            }

        except Exception as e:
            logger.exception("脱敏任务执行失败")
            # 更新执行状态为失败
            MaskingService.update_execution_status(
                db,
                execution_id,
                "FAILED",
                end_time=datetime.now(),
                error_message=str(e),
            )
            return {
                "success": False,
                "message": f"脱敏任务执行失败: {str(e)}",
            }

    # ==================== 脱敏算法 ====================

    @staticmethod
    def get_algorithms() -> List[Dict[str, Any]]:
        """获取所有脱敏算法"""
        return [
            {
                "code": algo.code,
                "name": algo.name,
                "description": algo.description,
                "params_schema": algo.params_schema,
            }
            for algo in PREDEFINED_ALGORITHMS
        ]
