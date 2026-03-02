"""
数据脱敏系统主入口
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
from app.api import api_router
from app.services.auth_service import AuthService

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_data():
    """初始化数据"""
    db = SessionLocal()
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        # 初始化默认数据
        AuthService.init_default_data(db)
    except Exception as e:
        logger.exception(f"初始化数据失败: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info(f"启动 {settings.APP_NAME}...")
    init_data()
    logger.info(f"{settings.APP_NAME} 启动完成")
    yield
    # 关闭时
    logger.info(f"{settings.APP_NAME} 正在关闭...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="恒丰银行数据脱敏系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None,
        },
    )


# 注册路由
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": settings.APP_NAME, "version": "1.0.0"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/api/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
