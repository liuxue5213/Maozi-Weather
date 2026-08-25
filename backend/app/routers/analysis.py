from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.weather import HistoryObservation
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/station")
async def analyze_station(
    station_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """站点统计分析：温度、降水统计"""
    # 查询指定时间范围的观测数据
    result = await db.execute(
        select(HistoryObservation)
        .where(
            HistoryObservation.station_id == station_id,
            HistoryObservation.observe_time >= start_time,
            HistoryObservation.observe_time <= end_time,
        )
        .order_by(HistoryObservation.observe_time)
    )
    observations = result.scalars().all()

    if not observations:
        return {"message": "该时间范围内无数据"}

    # 温度统计
    temperatures = [o.temperature for o in observations if o.temperature is not None]
    precipitations = [o.precipitation for o in observations if o.precipitation is not None and o.precipitation > 0]

    stats = {
        "station_id": station_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_records": len(observations),
        "missing_records": sum(1 for o in observations if o.is_missing),
        "temperature": {
            "max": max(temperatures) if temperatures else None,
            "min": min(temperatures) if temperatures else None,
            "avg": round(sum(temperatures) / len(temperatures), 2) if temperatures else None,
            "count": len(temperatures),
        },
        "precipitation": {
            "total": round(sum(precipitations), 2) if precipitations else 0,
            "rainy_days": len(precipitations),
        },
    }

    return stats


@router.get("/monthly")
async def monthly_analysis(
    station_id: str = Query(...),
    year: int = Query(..., ge=1950, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """月度统计（用于图表展示）"""
    result = await db.execute(
        select(
            extract("month", HistoryObservation.observe_time).label("month"),
            func.avg(HistoryObservation.temperature).label("avg_temp"),
            func.max(HistoryObservation.temperature).label("max_temp"),
            func.min(HistoryObservation.temperature).label("min_temp"),
            func.sum(HistoryObservation.precipitation).label("total_precip"),
            func.count().label("record_count"),
        )
        .where(
            HistoryObservation.station_id == station_id,
            extract("year", HistoryObservation.observe_time) == year,
        )
        .group_by(extract("month", HistoryObservation.observe_time))
        .order_by("month")
    )

    monthly_data = []
    for row in result.all():
        monthly_data.append({
            "month": int(row.month),
            "avg_temp": round(float(row.avg_temp or 0), 2),
            "max_temp": round(float(row.max_temp or 0), 2),
            "min_temp": round(float(row.min_temp or 0), 2),
            "total_precip": round(float(row.total_precip or 0), 2),
            "record_count": row.record_count,
        })

    return {
        "station_id": station_id,
        "year": year,
        "monthly": monthly_data,
    }
