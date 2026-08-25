"""
空气质量 & 生活指数 数据模型
"""
from datetime import datetime

from pydantic import BaseModel, Field


class AirQualityOut(BaseModel):
    """空气质量输出"""
    city_id: int
    station_id: str | None = None
    aqi: int | None = None
    aqi_level: str | None = None
    aqi_primary: str | None = None
    pm25: float | None = None
    pm10: float | None = None
    so2: float | None = None
    no2: float | None = None
    co: float | None = None
    o3: float | None = None
    data_type: str = "realtime"
    forecast_time: datetime | None = None
    data_source: str = "CMA"

    model_config = {"from_attributes": True}


class LifeIndexOut(BaseModel):
    """生活指数输出"""
    city_id: int
    index_type: str
    index_name: str
    index_level: str | None = None
    index_desc: str | None = None
    forecast_date: str | None = None

    model_config = {"from_attributes": True}


class AirQualityHistoryQuery(BaseModel):
    """空气质量历史查询"""
    city_id: int
    start_time: datetime
    end_time: datetime
