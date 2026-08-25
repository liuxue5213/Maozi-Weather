"""
空气质量数据模型
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AirQuality(Base):
    """空气质量（实况+预报）"""
    __tablename__ = "air_quality"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    station_id: Mapped[str | None] = mapped_column(String(20), index=True)
    # AQI
    aqi: Mapped[int | None] = mapped_column(Integer)  # AQI指数
    aqi_level: Mapped[str | None] = mapped_column(String(20))  # 空气质量等级
    aqi_primary: Mapped[str | None] = mapped_column(String(50))  # 首要污染物
    # 污染物浓度
    pm25: Mapped[float | None] = mapped_column(Float)  # PM2.5 (μg/m³)
    pm10: Mapped[float | None] = mapped_column(Float)  # PM10 (μg/m³)
    so2: Mapped[float | None] = mapped_column(Float)  # SO2 (μg/m³)
    no2: Mapped[float | None] = mapped_column(Float)  # NO2 (μg/m³)
    co: Mapped[float | None] = mapped_column(Float)  # CO (mg/m³)
    o3: Mapped[float | None] = mapped_column(Float)  # O3 (μg/m³)
    # 类型: realtime-实况, forecast-预报
    data_type: Mapped[str] = mapped_column(String(20), default="realtime")
    forecast_time: Mapped[datetime | None] = mapped_column(DateTime)  # 预报时间
    data_source: Mapped[str] = mapped_column(String(20), default="CMA")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LifeIndex(Base):
    """生活指数"""
    __tablename__ = "life_index"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    index_type: Mapped[str] = mapped_column(String(30))  # 指数类型
    index_name: Mapped[str] = mapped_column(String(50))  # 指数名称
    index_level: Mapped[str | None] = mapped_column(String(20))  # 等级
    index_desc: Mapped[str | None] = mapped_column(String(200))  # 描述
    forecast_date: Mapped[str | None] = mapped_column(String(10))  # 预报日期
    data_source: Mapped[str] = mapped_column(String(20), default="CMA")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
