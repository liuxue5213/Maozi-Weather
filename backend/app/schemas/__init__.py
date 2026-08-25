from app.schemas.user import UserLogin, UserOut, Token
from app.schemas.city import CityOut, UserCityOut, UserCityAdd
from app.schemas.weather import (
    WeatherRealtimeOut,
    WeatherForecastOut,
    WeatherWarningOut,
    HistorySyncTaskOut,
    HistorySyncTaskCreate,
    HistoryObservationOut,
    HistoryQuery,
)
from app.schemas.air_quality import AirQualityOut, LifeIndexOut, AirQualityHistoryQuery

__all__ = [
    "UserLogin",
    "UserOut",
    "Token",
    "CityOut",
    "UserCityOut",
    "UserCityAdd",
    "WeatherRealtimeOut",
    "WeatherForecastOut",
    "WeatherWarningOut",
    "HistorySyncTaskOut",
    "HistorySyncTaskCreate",
    "HistoryObservationOut",
    "HistoryQuery",
    "AirQualityOut",
    "LifeIndexOut",
    "AirQualityHistoryQuery",
]
