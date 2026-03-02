"""
Cloudberry Data Management Console - Main Application Entry
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
from app.api import api_router
from app.services.auth_service import AuthService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_data():
    """Initialize database data"""
    db = SessionLocal()
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        # Initialize default data
        AuthService.init_default_data(db)
    except Exception as e:
        logger.exception(f"Failed to initialize data: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    init_data()
    logger.info(f"{settings.APP_NAME} started successfully")
    yield
    # Shutdown
    logger.info(f"{settings.APP_NAME} is shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive data management platform with data masking, lineage analysis, and data synchronization capabilities.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"Internal server error: {str(exc)}",
            "data": None,
        },
    )


# Register routes
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": settings.APP_NAME, "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
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
