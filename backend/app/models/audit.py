"""
审计日志相关数据模型
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    """审计日志表"""

    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    user_id = Column(BigInteger, ForeignKey("sys_user.id"), index=True, comment="用户ID")
    username = Column(String(64), comment="用户名")
    operation_type = Column(String(32), index=True, comment="操作类型：LOGIN/LOGOUT/CREATE/UPDATE/DELETE/EXECUTE")
    operation_module = Column(String(64), index=True, comment="操作模块")
    operation_desc = Column(String(512), comment="操作描述")
    request_method = Column(String(16), comment="请求方法")
    request_url = Column(String(512), comment="请求URL")
    request_params = Column(JSON, comment="请求参数")
    response_result = Column(String(32), comment="响应结果：SUCCESS/FAIL")
    error_message = Column(Text, comment="错误信息")
    ip_address = Column(String(64), comment="IP地址")
    user_agent = Column(String(512), comment="User Agent")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="操作时间")

    # 关联
    user = relationship("User", back_populates="audit_logs")
