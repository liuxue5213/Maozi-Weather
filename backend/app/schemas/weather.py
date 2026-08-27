from datetime import datetime

from pydantic import BaseModel, Field


class WeatherRealtimeOut(BaseModel):
    city_id: int
    station_id: str | None = None
    temperature: float | None = None
    feels_like: float | None = None
    humidity: float | None = None
    pressure: float | None = None
    wind_direction: str | int | None = None
    wind_speed: float | None = None
    precipitation: float | None = None
    weather_desc: str | None = None
    observe_time: datetime | None = None
    data_source: str = "CMA"

    model_config = {"from_attributes": True}


class WeatherForecastOut(BaseModel):
    city_id: int
    forecast_type: str
    forecast_time: datetime
    temperature: float | None = None
    temp_max: float | None = None
    temp_min: float | None = None
    humidity: float | None = None
    weather_desc: str | None = None
    wind_direction: str | None = None
    wind_speed: float | None = None
    pop: float | None = None

    model_config = {"from_attributes": True}


class WeatherWarningOut(BaseModel):
    city_id: int
    warning_id: str | None = None
    warning_type: str | None = None
    warning_level: str | None = None
    title: str | None = None
    content: str | None = None
    publish_time: datetime | None = None
    effective: int = 1

    model_config = {"from_attributes": True}


class HistorySyncTaskCreate(BaseModel):
    station_id: str = Field(..., min_length=1, max_length=20)
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class HistorySyncTaskOut(BaseModel):
    id: int
    station_id: str
    start_date: str
    end_date: str
    status: str
    total_records: int
    fetched_records: int
    error_msg: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class HistoryQuery(BaseModel):
    station_id: str
    start_time: datetime
    end_time: datetime


class HistoryObservationOut(BaseModel):
    id: int
    station_id: str
    observe_time: datetime
    temperature: float | None = None
    pressure: float | None = None
    humidity: float | None = None
    wind_direction: float | None = None
    wind_speed: float | None = None
    precipitation: float | None = None
    is_missing: int = 0
    missing_fields: str | None = None

    model_config = {"from_attributes": True}
