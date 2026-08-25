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
