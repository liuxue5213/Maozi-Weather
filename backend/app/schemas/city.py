from datetime import datetime

from pydantic import BaseModel, Field


class CityOut(BaseModel):
    id: int
    city_name: str
    city_code: str | None = None
    station_id: str | None = None
    province: str | None = None
    longitude: float | None = None
    latitude: float | None = None

    model_config = {"from_attributes": True}


class UserCityOut(BaseModel):
    id: int
    city_id: int
    sort_order: int
    view_mode: str
    city: CityOut

    model_config = {"from_attributes": True}


class UserCityAdd(BaseModel):
    city_id: int
    view_mode: str = Field(default="city", pattern="^(city|station)$")


class CitySearch(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=50)


class CityCreate(BaseModel):
    """新增城市/站点"""
    city_name: str = Field(..., min_length=1, max_length=100)
    city_code: str | None = Field(None, max_length=20)
    station_id: str | None = Field(None, max_length=20)
    province: str | None = Field(None, max_length=50)
    longitude: float | None = Field(None, ge=-180, le=180)
    latitude: float | None = Field(None, ge=-90, le=90)


class CityUpdate(BaseModel):
    """修改城市信息（仅提交的字段生效）"""
    city_name: str | None = Field(None, min_length=1, max_length=100)
    city_code: str | None = Field(None, max_length=20)
    station_id: str | None = Field(None, max_length=20)
    province: str | None = Field(None, max_length=50)
    longitude: float | None = Field(None, ge=-180, le=180)
    latitude: float | None = Field(None, ge=-90, le=90)
