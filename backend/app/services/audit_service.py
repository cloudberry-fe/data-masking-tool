"""
审计日志服务
"""
import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """审计日志服务"""

    @staticmethod
    def log(
        db: Session,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        operation_type: Optional[str] = None,
        operation_module: Optional[str] = None,
        operation_desc: Optional[str] = None,
        request_method: Optional[str] = None,
        request_url: Optional[str] = None,
        request_params: Optional[Dict[str, Any]] = None,
        response_result: str = "SUCCESS",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """记录审计日志"""
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            operation_type=operation_type,
            operation_module=operation_module,
            operation_desc=operation_desc,
            request_method=request_method,
            request_url=request_url,
            request_params=request_params,
            response_result=response_result,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def get_logs(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        username: Optional[str] = None,
        operation_type: Optional[str] = None,
        operation_module: Optional[str] = None,
        response_result: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Tuple[List[AuditLog], int]:
        """获取审计日志列表"""
        query = select(AuditLog)

        conditions = []
        if username:
            conditions.append(AuditLog.username.contains(username))
        if operation_type:
            conditions.append(AuditLog.operation_type == operation_type)
        if operation_module:
            conditions.append(AuditLog.operation_module == operation_module)
        if response_result:
            conditions.append(AuditLog.response_result == response_result)
        if start_time:
            conditions.append(AuditLog.created_at >= start_time)
        if end_time:
            conditions.append(AuditLog.created_at <= end_time)

        if conditions:
            query = query.where(and_(*conditions))

        # 查询总数
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_stmt)

        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        logs = db.scalars(query).all()

        return logs, total

    @staticmethod
    def get_log(db: Session, log_id: int) -> Optional[AuditLog]:
        """获取审计日志详情"""
        stmt = select(AuditLog).where(AuditLog.id == log_id)
        return db.scalar(stmt)
