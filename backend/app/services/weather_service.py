"""
天气业务服务层

负责：
- 协调 Redis 缓存与 CMA API 调用
- 数据标准化处理
- 缺测标记
- 空气质量 & 生活指数
- 日出日落计算
"""

import json
import logging
from datetime import datetime, timedelta

from app.core.redis import get_redis
from app.utils.cma_client import cma_client
from app.services.air_quality_service import (
    calculate_aqi,
    calc_all_life_indices,
    calc_sunrise_sunset,
)

logger = logging.getLogger(__name__)

# 缓存过期时间（秒）
CACHE_TTL_REALTIME = 600       # 实况 10 分钟
CACHE_TTL_FORECAST = 3600      # 预报 1 小时
CACHE_TTL_WARNING = 300        # 预警 5 分钟
CACHE_TTL_AIR_QUALITY = 1800    # 空气质量 30 分钟
CACHE_TTL_LIFE_INDEX = 3600     # 生活指数 1 小时


class WeatherService:
    """天气数据服务"""

    @staticmethod
    async def get_realtime(city_id: int, station_id: str | None = None) -> dict | None:
        """
        获取实况天气（缓存优先）

        流程：
        1. 先查 Redis 缓存
        2. 无缓存则调用 CMA 接口
        3. 写入缓存后返回
        """
        redis = await get_redis()
        cache_key = f"weather:realtime:{city_id}"

        # 1. 查缓存
        cached = await redis.get(cache_key)
        if cached:
            logger.debug(f"实况缓存命中: city_id={city_id}")
            return json.loads(cached)

        # 2. 调用 CMA
        if not station_id:
            # TODO: 从数据库获取站点ID
            return None

        try:
            data = await cma_client.get_realtime(station_id)
        except Exception as e:
            logger.error(f"获取实况失败: city_id={city_id}, error={e}")
            return None

        # 3. 标准化处理
        result = WeatherService._normalize_realtime(city_id, data)

        # 4. 写入缓存
        if result:
            await redis.setex(cache_key, CACHE_TTL_REALTIME, json.dumps(result, default=str))

        return result

    @staticmethod
    async def get_forecast(city_id: int, city_code: str | None = None) -> list[dict]:
        """获取天气预报（缓存优先）"""
        redis = await get_redis()
        cache_key = f"weather:forecast:{city_id}"

        # 1. 查缓存
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # 2. 调用 CMA
        if not city_code:
            return []

        try:
            data = await cma_client.get_forecast(city_code)
        except Exception as e:
            logger.error(f"获取预报失败: city_id={city_id}, error={e}")
            return []

        # 3. 标准化
        result = WeatherService._normalize_forecast(city_id, data)

        # 4. 缓存
        if result:
            await redis.setex(cache_key, CACHE_TTL_FORECAST, json.dumps(result, default=str))

        return result

    @staticmethod
    async def get_warning(city_id: int, city_code: str | None = None) -> list[dict]:
        """获取气象预警（缓存优先）"""
        redis = await get_redis()
        cache_key = f"weather:warning:{city_id}"

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        if not city_code:
            return []

        try:
            data = await cma_client.get_warning(city_code)
        except Exception as e:
            logger.error(f"获取预警失败: city_id={city_id}, error={e}")
            return []

        result = WeatherService._normalize_warning(city_id, data)

        if result:
            await redis.setex(cache_key, CACHE_TTL_WARNING, json.dumps(result, default=str))

        return result

    @staticmethod
    async def get_air_quality(city_id: int, station_id: str | None = None) -> dict | None:
        """获取空气质量（缓存优先）"""
        redis = await get_redis()
        cache_key = f"weather:air_quality:{city_id}"

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # TODO: 调用 CMA 空气质量接口
        # 暂时返回 None，等待接口对接
        return None

    @staticmethod
    async def get_life_index(city_id: int, temperature: float = 20,
                             humidity: float = 50, precipitation: float = 0,
                             wind_speed: float = 0, uv: float = 5) -> list[dict]:
        """
        获取生活指数

        生活指数基于气象数据计算，不需要调用外部接口
        """
        return calc_all_life_indices(temperature, humidity, precipitation, wind_speed, uv)

    @staticmethod
    def get_sunrise_sunset(latitude: float, longitude: float, date: datetime = None) -> dict:
        """
        获取日出日落时间

        基于经纬度和日期计算
        """
        return calc_sunrise_sunset(latitude, longitude, date)

    @staticmethod
    def calc_aqi(pm25=None, pm10=None, so2=None, no2=None, co=None, o3=None) -> dict:
        """
        计算 AQI
        """
        return calculate_aqi(pm25, pm10, so2, no2, co, o3)

    @staticmethod
    def _normalize_realtime(city_id: int, raw_data: dict) -> dict | None:
        """标准化实况数据（根据 CMA 实际返回格式调整）"""
        if not raw_data or not raw_data.get("data"):
            return None

        d = raw_data["data"]
        return {
            "city_id": city_id,
            "station_id": d.get("stationid"),
            "temperature": d.get("temperature"),
            "feels_like": d.get("feelsLike"),
            "humidity": d.get("humidity"),
            "pressure": d.get("pressure"),
            "wind_direction": d.get("windDirection"),
            "wind_speed": d.get("windSpeed"),
            "precipitation": d.get("precipitation"),
            "weather_desc": d.get("weather"),
            "observe_time": d.get("observeTime"),
            "data_source": "CMA",
        }

    @staticmethod
    def _normalize_forecast(city_id: int, raw_data: dict) -> list[dict]:
        """标准化预报数据"""
        if not raw_data or not raw_data.get("data"):
            return []

        result = []
        for item in raw_data["data"]:
            result.append({
                "city_id": city_id,
                "forecast_type": item.get("type", "daily"),
                "forecast_time": item.get("forecastTime"),
                "temperature": item.get("temperature"),
                "temp_max": item.get("tempMax"),
                "temp_min": item.get("tempMin"),
                "humidity": item.get("humidity"),
                "weather_desc": item.get("weather"),
                "wind_direction": item.get("windDirection"),
                "wind_speed": item.get("windSpeed"),
                "pop": item.get("pop"),
            })
        return result

    @staticmethod
    def _normalize_warning(city_id: int, raw_data: dict) -> list[dict]:
        """标准化预警数据"""
        if not raw_data or not raw_data.get("data"):
            return []

        result = []
        for item in raw_data["data"]:
            result.append({
                "city_id": city_id,
                "warning_id": item.get("warningId"),
                "warning_type": item.get("type"),
                "warning_level": item.get("level"),
                "title": item.get("title"),
                "content": item.get("content"),
                "publish_time": item.get("publishTime"),
                "effective": 1,
            })
        return result


weather_service = WeatherService()
