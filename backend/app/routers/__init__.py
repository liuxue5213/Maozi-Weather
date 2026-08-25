from fastapi import APIRouter

from app.routers import auth, city, weather, history, analysis, air_quality

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["鉴权"])
api_router.include_router(city.router, prefix="/cities", tags=["城市"])
api_router.include_router(weather.router, prefix="/weather", tags=["天气"])
api_router.include_router(history.router, prefix="/history", tags=["历史数据"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["数据分析"])
api_router.include_router(air_quality.router, prefix="/air", tags=["空气质量"])
