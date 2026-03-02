"""
API v1 路由
"""
from fastapi import APIRouter

from app.api.v1 import auth, datasource, masking, system, lineage, sync, audit

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, tags=["认证"])
api_router.include_router(datasource.router, prefix="/datasources", tags=["数据源管理"])
api_router.include_router(masking.router, prefix="/masking", tags=["数据脱敏"])
api_router.include_router(lineage.router, prefix="/lineage", tags=["血缘分析"])
api_router.include_router(sync.router, prefix="/sync", tags=["翻数工具"])
api_router.include_router(system.router, prefix="/system", tags=["系统管理"])
api_router.include_router(audit.router, prefix="/audit", tags=["审计日志"])
