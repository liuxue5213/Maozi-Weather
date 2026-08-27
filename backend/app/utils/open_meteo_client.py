"""
Open-Meteo 天气 API 客户端

免费、无需注册、无需 API Key
- 每日 10,000 次免费调用
- 全球覆盖，国内可用
- 支持实况、预报（16天）、历史数据、空气质量

官网: https://open-meteo.com
文档: https://open-meteo.com/en/docs
"""

import logging
from datetime import datetime

import httpx

from app.core.config import settings
from app.services.air_quality_service import calculate_aqi

logger = logging.getLogger(__name__)

BASE_URL = "https://api.open-meteo.com/v1"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1"


class OpenMeteoClient:
    """Open-Meteo API 客户端"""

    def __init__(self):
        self.base_url = BASE_URL
        self.archive_url = ARCHIVE_URL
        self.air_quality_url = AIR_QUALITY_URL
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "MaoZi-Weather/0.1.0"},
            )
        return self._client

    async def close(self):
        """关闭连接"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, base_url: str, endpoint: str, params: dict) -> dict:
        """通用请求方法"""
        client = await self.get_client()
        url = f"{base_url}/{endpoint}"

        logger.debug(f"Open-Meteo 请求: {endpoint} params={params}")

        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        current: list[str] | None = None,
        hourly: list[str] | None = None,
        daily: list[str] | None = None,
        forecast_days: int = 16,
        timezone: str = "Asia/Shanghai",
    ) -> dict:
        """
        获取天气预报（支持16天）

        Args:
            latitude: 纬度
            longitude: 经度
            current: 当前天气变量列表
            hourly: 逐小时变量列表
            daily: 逐日变量列表
            forecast_days: 预报天数（1-16天）
            timezone: 时区
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": min(forecast_days, 16),
        }

        if current:
            params["current"] = ",".join(current)
        if hourly:
            params["hourly"] = ",".join(hourly)
        if daily:
            params["daily"] = ",".join(daily)

        return await self._request(self.base_url, "forecast", params)

    async def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        daily: list[str] | None = None,
        timezone: str = "Asia/Shanghai",
    ) -> dict:
        """
        获取历史天气数据

        Args:
            latitude: 纬度
            longitude: 经度
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            daily: 逐日变量列表
            timezone: 时区
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,
        }

        if daily:
            params["daily"] = ",".join(daily)

        return await self._request(self.archive_url, "archive", params)

    async def get_air_quality(
        self,
        latitude: float,
        longitude: float,
        current: list[str] | None = None,
        timezone: str = "Asia/Shanghai",
    ) -> dict:
        """
        获取空气质量数据

        Args:
            latitude: 纬度
            longitude: 经度
            current: 空气质量变量列表
            timezone: 时区
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
        }

        if current:
            params["current"] = ",".join(current)

        return await self._request(self.air_quality_url, "air-quality", params)

    # ===== 数据标准化方法 =====

    @staticmethod
    def normalize_current_weather(data: dict, city_id: int) -> dict | None:
        """
        标准化当前天气数据

        Open-Meteo 返回格式:
        {
            "current": {
                "time": "2024-01-01T12:00",
                "temperature_2m": 25.0,
                "relative_humidity_2m": 60,
                "weather_code": 1,
                "wind_speed_10m": 10.5,
                ...
            }
        }
        """
        if not data or "current" not in data:
            return None

        current = data["current"]

        # WMO Weather interpretation codes
        weather_codes = {
            0: "晴",
            1: "大部晴朗", 2: "多云", 3: "阴天",
            45: "雾", 48: "雾凇",
            51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            77: "雪粒",
            80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
            85: "小阵雪", 86: "大阵雪",
            95: "雷暴", 96: "雷暴+小冰雹", 99: "雷暴+大冰雹",
        }

        weather_code = current.get("weather_code", 0)

        return {
            "city_id": city_id,
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "pressure": current.get("surface_pressure"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "precipitation": current.get("precipitation"),
            "weather_desc": weather_codes.get(weather_code, "未知"),
            "observe_time": current.get("time"),
            "data_source": "Open-Meteo",
        }

    @staticmethod
    def normalize_daily_forecast(data: dict, city_id: int) -> list[dict]:
        """
        标准化逐日预报数据

        Open-Meteo 返回格式:
        {
            "daily": {
                "time": ["2024-01-01", ...],
                "weather_code": [1, ...],
                "temperature_2m_max": [25.0, ...],
                "temperature_2m_min": [15.0, ...],
                ...
            }
        }
        """
        if not data or "daily" not in data:
            return []

        daily = data["daily"]
        dates = daily.get("time", [])

        weather_codes = {
            0: "晴", 1: "大部晴朗", 2: "多云", 3: "阴天",
            45: "雾", 48: "雾凇",
            51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
            95: "雷暴", 96: "雷暴+小冰雹", 99: "雷暴+大冰雹",
        }

        result = []
        for i, date in enumerate(dates):
            weather_code = daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0

            result.append({
                "city_id": city_id,
                "forecast_type": "daily",
                "forecast_time": f"{date}T00:00:00",
                "temp_max": daily.get("temperature_2m_max", [None])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                "temp_min": daily.get("temperature_2m_min", [None])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                "weather_desc": weather_codes.get(weather_code, "未知"),
                "precipitation_sum": daily.get("precipitation_sum", [None])[i] if i < len(daily.get("precipitation_sum", [])) else None,
                "wind_speed_max": daily.get("wind_speed_10m_max", [None])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
                "sunrise": daily.get("sunrise", [None])[i] if i < len(daily.get("sunrise", [])) else None,
                "sunset": daily.get("sunset", [None])[i] if i < len(daily.get("sunset", [])) else None,
                "data_source": "Open-Meteo",
            })

        return result

    @staticmethod
    def normalize_hourly_forecast(data: dict, city_id: int) -> list[dict]:
        """
        标准化逐小时预报数据
        """
        if not data or "hourly" not in data:
            return []

        hourly = data["hourly"]
        times = hourly.get("time", [])

        weather_codes = {
            0: "晴", 1: "大部晴朗", 2: "多云", 3: "阴天",
            45: "雾", 48: "雾凇",
            51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
            95: "雷暴", 96: "雷暴+小冰雹", 99: "雷暴+大冰雹",
        }

        result = []
        for i, time in enumerate(times):
            weather_code = hourly.get("weather_code", [0])[i] if i < len(hourly.get("weather_code", [])) else 0

            result.append({
                "city_id": city_id,
                "forecast_type": "hourly",
                "forecast_time": time.replace("T", " ") + ":00",
                "temperature": hourly.get("temperature_2m", [None])[i] if i < len(hourly.get("temperature_2m", [])) else None,
                "humidity": hourly.get("relative_humidity_2m", [None])[i] if i < len(hourly.get("relative_humidity_2m", [])) else None,
                "weather_desc": weather_codes.get(weather_code, "未知"),
                "precipitation": hourly.get("precipitation", [None])[i] if i < len(hourly.get("precipitation", [])) else None,
                "wind_speed": hourly.get("wind_speed_10m", [None])[i] if i < len(hourly.get("wind_speed_10m", [])) else None,
                "data_source": "Open-Meteo",
            })

        return result

    @staticmethod
    def normalize_air_quality(data: dict, city_id: int) -> dict | None:
        """
        标准化空气质量数据

        Open-Meteo 返回格式:
        {
            "current": {
                "time": "2024-01-01T12:00",
                "european_aqi": 42,
                "pm10": 15.2,
                "pm2_5": 8.5,
                "carbon_monoxide": 200,
                "nitrogen_dioxide": 20,
                "sulphur_dioxide": 5,
                "ozone": 80,
                ...
            }
        }
        """
        if not data or "current" not in data:
            return None

        current = data["current"]

        # 用污染物浓度换算国标 AQI（GB 3095-2012）
        # Open-Meteo 单位: pm2_5/pm10/so2/no2/o3 为 µg/m³，carbon_monoxide 为 µg/m³
        # 国标 CO 浓度限值为 mg/m³，需 ÷1000
        co = current.get("carbon_monoxide")
        co = co / 1000.0 if co is not None else None
        cn = calculate_aqi(
            pm25=current.get("pm2_5"),
            pm10=current.get("pm10"),
            so2=current.get("sulphur_dioxide"),
            no2=current.get("nitrogen_dioxide"),
            co=co,
            o3=current.get("ozone"),
        )

        return {
            "city_id": city_id,
            "aqi": cn["aqi"],
            "aqi_level": cn["level"],
            "aqi_primary": cn["primary"],
            "pm25": current.get("pm2_5"),
            "pm10": current.get("pm10"),
            "co": current.get("carbon_monoxide"),
            "no2": current.get("nitrogen_dioxide"),
            "so2": current.get("sulphur_dioxide"),
            "o3": current.get("ozone"),
            "us_aqi": current.get("us_aqi"),
            "data_source": "Open-Meteo",
        }


# 全局单例
open_meteo_client = OpenMeteoClient()
