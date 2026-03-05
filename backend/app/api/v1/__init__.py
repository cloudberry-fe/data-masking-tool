"""
API v1 路由
"""
from fastapi import APIRouter

from app.api.v1 import auth, datasource, masking, system, lineage, sync, audit
from app.api.v1 import dynamic_masking, anonymization, test_data

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, tags=["认证"])
api_router.include_router(datasource.router, prefix="/datasources", tags=["数据源管理"])
api_router.include_router(masking.router, prefix="/masking", tags=["静态脱敏"])
api_router.include_router(dynamic_masking.router, prefix="/dynamic-masking", tags=["动态脱敏"])
api_router.include_router(anonymization.router, prefix="/anonymization", tags=["原地匿名化"])
api_router.include_router(lineage.router, prefix="/lineage", tags=["血缘分析"])
api_router.include_router(sync.router, prefix="/sync", tags=["翻数工具"])
api_router.include_router(test_data.router, prefix="/test-data", tags=["测试数据生成"])
api_router.include_router(system.router, prefix="/system", tags=["系统管理"])
api_router.include_router(audit.router, prefix="/audit", tags=["审计日志"])
