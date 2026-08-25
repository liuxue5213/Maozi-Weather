"""
空气质量 & 生活指数 API
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.air_quality import AirQuality, LifeIndex
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.air_quality import AirQualityOut, LifeIndexOut

router = APIRouter()


@router.get("/realtime/{city_id}", response_model=AirQualityOut)
async def get_air_quality_realtime(
    city_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市实时空气质量"""
    result = await db.execute(
        select(AirQuality)
        .where(
            AirQuality.city_id == city_id,
            AirQuality.data_type == "realtime",
        )
        .order_by(AirQuality.created_at.desc())
        .limit(1)
    )
    data = result.scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404, detail="暂无空气质量数据")
    return data


@router.get("/forecast/{city_id}", response_model=list[AirQualityOut])
async def get_air_quality_forecast(
    city_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市空气质量预报"""
    result = await db.execute(
        select(AirQuality)
        .where(
            AirQuality.city_id == city_id,
            AirQuality.data_type == "forecast",
        )
        .order_by(AirQuality.forecast_time)
    )
    return result.scalars().all()


@router.get("/history/{city_id}", response_model=list[AirQualityOut])
async def get_air_quality_history(
    city_id: int,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询城市历史空气质量"""
    result = await db.execute(
        select(AirQuality)
        .where(
            AirQuality.city_id == city_id,
            AirQuality.data_type == "realtime",
            AirQuality.created_at >= start_time,
            AirQuality.created_at <= end_time,
        )
        .order_by(AirQuality.created_at)
    )
    return result.scalars().all()


@router.get("/life_index/{city_id}", response_model=list[LifeIndexOut])
async def get_life_index(
    city_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市生活指数"""
    result = await db.execute(
        select(LifeIndex)
        .where(LifeIndex.city_id == city_id)
        .order_by(LifeIndex.index_type)
    )
    return result.scalars().all()
