"""
天气 API 路由（多源）

使用多源天气服务，自动切换/备份：
- Open-Meteo：主数据源（免费、无需注册）
- QWeather：增强数据源（空气质量、预警、生活指数）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.weather import (
    WeatherForecastOut,
    WeatherRealtimeOut,
    WeatherWarningOut,
)
from app.schemas.air_quality import AirQualityOut, LifeIndexOut
from app.services.multi_source_weather import multi_source_weather

router = APIRouter()


@router.get("/realtime/{city_id}", response_model=WeatherRealtimeOut)
async def get_realtime(
    city_id: int,
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市实时天气（多源）"""
    result = await multi_source_weather.get_realtime(city_id, latitude, longitude)
    if not result:
        raise HTTPException(status_code=404, detail="无法获取实时天气数据")
    return result


@router.get("/forecast/{city_id}")
async def get_forecast(
    city_id: int,
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    days: int = Query(16, ge=1, le=16, description="预报天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市预报（多源，支持16天）"""
    result = await multi_source_weather.get_forecast(city_id, latitude, longitude, days=days)
    if not result.get("daily"):
        raise HTTPException(status_code=404, detail="无法获取预报数据")
    return result


@router.get("/warning/{city_id}", response_model=list[WeatherWarningOut])
async def get_warning(
    city_id: int,
    location_id: str | None = Query(None, description="和风天气 LocationID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市气象预警"""
    result = await multi_source_weather.get_warning(city_id, location_id)
    return result


# ===== 空气质量 & 生活指数 & 日出日落 =====

@router.get("/air_quality/{city_id}", response_model=AirQualityOut)
async def get_air_quality(
    city_id: int,
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市空气质量（多源）"""
    result = await multi_source_weather.get_air_quality(city_id, latitude, longitude)
    if not result:
        raise HTTPException(status_code=404, detail="暂无空气质量数据")
    return result


@router.get("/life_index/{city_id}", response_model=list[LifeIndexOut])
async def get_life_index(
    city_id: int,
    temperature: float = Query(20.0, description="当前温度"),
    humidity: float = Query(50.0, description="当前湿度"),
    precipitation: float = Query(0.0, description="降水量"),
    wind_speed: float = Query(0.0, description="风速"),
    uv: float = Query(5.0, description="紫外线指数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市生活指数（多源）"""
    indices = await multi_source_weather.get_life_index(
        city_id, temperature, humidity, precipitation, wind_speed, uv
    )
    return indices


@router.get("/sun/{city_id}")
async def get_sunrise_sunset(
    city_id: int,
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取日出日落时间"""
    result = multi_source_weather.get_sunrise_sunset(latitude, longitude)
    return result


@router.get("/aqi/calculate")
async def calculate_aqi(
    pm25: float | None = Query(None, description="PM2.5浓度"),
    pm10: float | None = Query(None, description="PM10浓度"),
    so2: float | None = Query(None, description="SO2浓度"),
    no2: float | None = Query(None, description="NO2浓度"),
    co: float | None = Query(None, description="CO浓度"),
    o3: float | None = Query(None, description="O3浓度"),
    current_user: User = Depends(get_current_user),
):
    """计算 AQI（根据污染物浓度）"""
    from app.services.air_quality_service import calculate_aqi
    result = calculate_aqi(pm25, pm10, so2, no2, co, o3)
    return result


@router.get("/historical/{city_id}")
async def get_historical(
    city_id: int,
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取历史天气数据"""
    result = await multi_source_weather.get_historical(
        city_id, latitude, longitude, start_date, end_date
    )
    return result
