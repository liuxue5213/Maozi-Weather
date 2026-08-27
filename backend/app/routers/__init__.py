from fastapi import APIRouter

from app.routers import (
    air_quality,
    analysis,
    auth,
    city,
    history,
    logs,
    public,
    system,
    weather,
)

api_router = APIRouter()

# 公开接口（无需登录）
api_router.include_router(public.router, prefix="/public", tags=["公开"])

# 需要登录的接口
api_router.include_router(auth.router, prefix="/auth", tags=["鉴权"])
api_router.include_router(city.router, prefix="/cities", tags=["城市"])
api_router.include_router(weather.router, prefix="/weather", tags=["天气"])
api_router.include_router(history.router, prefix="/history", tags=["历史数据"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["数据分析"])
api_router.include_router(air_quality.router, prefix="/air", tags=["空气质量"])
api_router.include_router(system.router, prefix="/system", tags=["系统"])
api_router.include_router(logs.router, prefix="/logs", tags=["日志"])
