import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.log import ApiCallLog
from app.routers import api_router
from app.services.scheduler import init_scheduler, shutdown_scheduler

# 日志配置
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"🚀 {settings.APP_NAME} 启动中...")
    logger.info(f"环境: {settings.APP_ENV}")
    await init_scheduler()
    yield
    # 关闭时清理
    await shutdown_scheduler()
    logger.info("👋 应用关闭中...")


app = FastAPI(
    title=settings.APP_NAME,
    description="帽子天气 - 气象数据应用系统后端 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 配置
def _resolve_cors_origins() -> list:
    raw = settings.CORS_ORIGINS
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    # 开发环境放开全部来源；生产环境必须显式配置 CORS_ORIGINS
    return ["*"] if settings.APP_DEBUG else []


_CORS_ORIGINS = _resolve_cors_origins()
# 允许携带凭据时不能使用通配符来源（Starlette 会拒绝），故通配时关闭 credentials
_CORS_CREDENTIALS = _CORS_ORIGINS != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=_CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix=settings.APP_V1_PREFIX)


@app.middleware("http")
async def api_call_logging(request: Request, call_next):
    """API 调用日志中间件：将 /api 请求概要写入 api_call_logs 表"""
    path = request.url.path
    if not path.startswith(settings.APP_V1_PREFIX):
        return await call_next(request)

    started = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        try:
            async with AsyncSessionLocal() as db:
                db.add(ApiCallLog(
                    endpoint=path[:200],
                    params=str(dict(request.query_params))[:500] if request.query_params else None,
                    status_code=response.status_code,
                    response_time=elapsed_ms,
                    error_msg=None,
                ))
                await db.commit()
        except Exception as log_err:  # 日志落库失败不影响业务响应
            logger.warning(f"API 日志写入失败: {log_err}")
        return response
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        try:
            async with AsyncSessionLocal() as db:
                db.add(ApiCallLog(
                    endpoint=path[:200],
                    params=str(dict(request.query_params))[:500] if request.query_params else None,
                    status_code=500,
                    response_time=elapsed_ms,
                    error_msg=str(exc)[:500],
                ))
                await db.commit()
        except Exception:
            pass
        raise


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }
