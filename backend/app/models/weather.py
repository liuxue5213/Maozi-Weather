from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherRealtime(Base):
    """实况天气（缓存最新一条）"""
    __tablename__ = "weather_realtime"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    station_id: Mapped[str | None] = mapped_column(String(20), index=True)
    temperature: Mapped[float | None] = mapped_column(Float)  # 温度(℃)
    feels_like: Mapped[float | None] = mapped_column(Float)  # 体感温度
    humidity: Mapped[float | None] = mapped_column(Float)  # 湿度(%)
    pressure: Mapped[float | None] = mapped_column(Float)  # 气压(hPa)
    wind_direction: Mapped[str | None] = mapped_column(String(20))  # 风向
    wind_speed: Mapped[float | None] = mapped_column(Float)  # 风速(m/s)
    precipitation: Mapped[float | None] = mapped_column(Float)  # 降水量(mm)
    weather_desc: Mapped[str | None] = mapped_column(String(50))  # 天气描述
    observe_time: Mapped[datetime | None] = mapped_column(DateTime)  # 观测时间
    data_source: Mapped[str] = mapped_column(String(20), default="CMA")  # 数据来源
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_realtime_city_observe", "city_id", "observe_time"),
    )


class WeatherForecast(Base):
    """天气预报（逐小时/逐日）"""
    __tablename__ = "weather_forecast"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    forecast_type: Mapped[str] = mapped_column(String(10))  # hourly | daily
    forecast_time: Mapped[datetime] = mapped_column(DateTime)  # 预报目标时间
    temperature: Mapped[float | None] = mapped_column(Float)
    temp_max: Mapped[float | None] = mapped_column(Float)
    temp_min: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    weather_desc: Mapped[str | None] = mapped_column(String(50))
    wind_direction: Mapped[str | None] = mapped_column(String(20))
    wind_speed: Mapped[float | None] = mapped_column(Float)
    pop: Mapped[float | None] = mapped_column(Float)  # 降水概率
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_forecast_city_type_time", "city_id", "forecast_type", "forecast_time"),
    )


class WeatherWarning(Base):
    """气象预警"""
    __tablename__ = "weather_warning"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    warning_id: Mapped[str | None] = mapped_column(String(50), unique=True)  # 官方预警ID
    warning_type: Mapped[str | None] = mapped_column(String(50))  # 预警类型：暴雨、大风等
    warning_level: Mapped[str | None] = mapped_column(String(20))  # 预警级别：蓝色、黄色、橙色、红色
    title: Mapped[str | None] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text)
    publish_time: Mapped[datetime | None] = mapped_column(DateTime)
    effective: Mapped[int] = mapped_column(Integer, default=1)  # 是否生效中
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class HistorySyncTask(Base):
    """历史数据同步任务"""
    __tablename__ = "history_sync_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    start_date: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD
    end_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | running | completed | failed | stopped
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    fetched_records: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class HistoryObservation(Base):
    """历史气象观测数据（时序数据）"""
    __tablename__ = "history_observations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(20), nullable=False)
    observe_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float)
    pressure: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    wind_direction: Mapped[float | None] = mapped_column(Float)  # 风向角度
    wind_speed: Mapped[float | None] = mapped_column(Float)
    precipitation: Mapped[float | None] = mapped_column(Float)
    is_missing: Mapped[int] = mapped_column(Integer, default=0)  # 是否缺测
    missing_fields: Mapped[str | None] = mapped_column(String(200))  # 缺测字段列表
    data_source: Mapped[str] = mapped_column(String(20), default="CMA")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        # 站点+时间唯一约束，防止重复入库
        Index("ix_obs_station_time", "station_id", "observe_time", unique=True),
        # 时间范围查询索引
        Index("ix_obs_time", "observe_time"),
    )
