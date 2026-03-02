"""
API依赖项
"""
import logging
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.system import User
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_token_credentials(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """获取Token凭证"""
    if credentials:
        return credentials.credentials
    return None


async def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(get_token_credentials),
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = AuthService.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if current_user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    return current_user


async def get_optional_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(get_token_credentials),
) -> Optional[User]:
    """获取可选的当前用户（用于审计日志）"""
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        return None

    return AuthService.get_user_by_id(db, int(user_id))


async def audit_logger(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """审计日志记录器（依赖注入用）"""
    # 这个函数不直接记录，而是返回一个记录函数
    def log(
        operation_type: str,
        operation_module: str,
        operation_desc: str,
        response_result: str = "SUCCESS",
        error_message: Optional[str] = None,
    ):
        try:
            AuditService.log(
                db=db,
                user_id=current_user.id if current_user else None,
                username=current_user.username if current_user else None,
                operation_type=operation_type,
                operation_module=operation_module,
                operation_desc=operation_desc,
                request_method=request.method,
                request_url=str(request.url),
                response_result=response_result,
                error_message=error_message,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception as e:
            logger.exception(f"记录审计日志失败: {e}")

    return log


# 类型别名
CurrentUser = Annotated[User, Depends(get_current_active_user)]
DBSession = Annotated[Session, Depends(get_db)]
AuditLogger = Annotated[callable, Depends(audit_logger)]
