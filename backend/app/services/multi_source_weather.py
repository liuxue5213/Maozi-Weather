"""
多源天气数据服务

统一接口，自动切换/备份多个数据源：
- Open-Meteo：免费、无需注册，作为主数据源
- QWeather（和风天气）：国内最全面，作为增强数据源
- CMA（中国气象数据网）：官方数据，作为权威备份

策略：
1. 优先使用 Open-Meteo（免费、稳定）
2. QWeather 用于补充空气质量、预警、生活指数
3. 任一源失败时自动切换到其他源
"""

import logging
from datetime import datetime, timedelta

from app.core.redis import get_redis
from app.utils.open_meteo_client import open_meteo_client
from app.utils.qweather_client import qweather_client, QWeatherError
from app.services.air_quality_service import calc_all_life_indices, calc_sunrise_sunset

logger = logging.getLogger(__name__)

# 缓存过期时间（秒）
CACHE_TTL_REALTIME = 600       # 实况 10 分钟
CACHE_TTL_FORECAST = 3600      # 预报 1 小时
CACHE_TTL_WARNING = 300        # 预警 5 分钟
CACHE_TTL_AIR_QUALITY = 1800    # 空气质量 30 分钟
CACHE_TTL_LIFE_INDEX = 3600     # 生活指数 1 小时


class MultiSourceWeatherService:
    """多源天气数据服务"""

    @staticmethod
    async def get_realtime(city_id: int, latitude: float, longitude: float,
                           location_id: str | None = None) -> dict | None:
        """
        获取实时天气（多源）

        优先 Open-Meteo，失败时尝试 QWeather
        """
        redis = await get_redis()
        cache_key = f"weather:realtime:{city_id}"

        # 1. 查缓存
        cached = await redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        result = None

        # 2. 尝试 Open-Meteo
        try:
            data = await open_meteo_client.get_forecast(
                latitude=latitude,
                longitude=longitude,
                current=[
                    "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                    "weather_code", "wind_speed_10m", "wind_direction_10m",
                    "precipitation", "surface_pressure",
                ],
            )
            result = open_meteo_client.normalize_current_weather(data, city_id)
            logger.info(f"Open-Meteo 实时天气获取成功: city_id={city_id}")
        except Exception as e:
            logger.warning(f"Open-Meteo 实时天气失败: {e}")

        # 3. Open-Meteo 失败，尝试 QWeather
        if not result and location_id:
            try:
                data = await qweather_client.get_realtime_weather(location_id)
                result = qweather_client.normalize_realtime(data, city_id)
                logger.info(f"QWeather 实时天气获取成功: city_id={city_id}")
            except Exception as e:
                logger.warning(f"QWeather 实时天气失败: {e}")

        # 4. 写入缓存
        if result:
            import json
            await redis.setex(cache_key, CACHE_TTL_REALTIME, json.dumps(result, default=str))

        return result

    @staticmethod
    async def get_forecast(city_id: int, latitude: float, longitude: float,
                           location_id: str | None = None, days: int = 16) -> dict:
        """
        获取天气预报（多源）

        Returns:
            dict: {daily: [...], hourly: [...], sun: {...}}
        """
        redis = await get_redis()
        cache_key = f"weather:forecast:{city_id}"

        # 1. 查缓存
        cached = await redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        result = {"daily": [], "hourly": [], "sun": None}

        # 2. 尝试 Open-Meteo（支持16天）
        try:
            data = await open_meteo_client.get_forecast(
                latitude=latitude,
                longitude=longitude,
                hourly=["temperature_2m", "relative_humidity_2m", "weather_code",
                        "precipitation", "wind_speed_10m"],
                daily=["weather_code", "temperature_2m_max", "temperature_2m_min",
                       "precipitation_sum", "wind_speed_10m_max",
                       "sunrise", "sunset"],
                forecast_days=days,
            )
            # 注意：hourly 和 daily 是分开的参数，不是嵌套关系

            result["daily"] = open_meteo_client.normalize_daily_forecast(data, city_id)
            result["hourly"] = open_meteo_client.normalize_hourly_forecast(data, city_id)

            # 提取日出日落
            if data.get("daily", {}).get("sunrise"):
                result["sun"] = {
                    "sunrise": data["daily"]["sunrise"][0],
                    "sunset": data["daily"]["sunset"][0],
                }

            logger.info(f"Open-Meteo 预报获取成功: city_id={city_id}, days={days}")
        except Exception as e:
            logger.warning(f"Open-Meteo 预报失败: {e}")

        # 3. Open-Meteo 失败，尝试 QWeather
        if not result["daily"] and location_id:
            try:
                # QWeather 最多支持15天
                qw_days = min(days, 15)
                daily_data = await qweather_client.get_daily_forecast(location_id, qw_days)
                result["daily"] = qweather_client.normalize_daily_forecast(daily_data, city_id)

                # 逐小时
                hourly_data = await qweather_client.get_hourly_forecast(location_id, 24)
                result["hourly"] = qweather_client.normalize_hourly_forecast(hourly_data, city_id)

                logger.info(f"QWeather 预报获取成功: city_id={city_id}")
            except Exception as e:
                logger.warning(f"QWeather 预报失败: {e}")

        # 4. 写入缓存
        if result["daily"]:
            import json
            await redis.setex(cache_key, CACHE_TTL_FORECAST, json.dumps(result, default=str))

        return result

    @staticmethod
    async def get_air_quality(city_id: int, latitude: float, longitude: float,
                              location_id: str | None = None) -> dict | None:
        """
        获取空气质量（多源）

        优先 Open-Meteo，失败时尝试 QWeather
        """
        redis = await get_redis()
        cache_key = f"weather:air_quality:{city_id}"

        # 1. 查缓存
        cached = await redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        result = None

        # 2. 尝试 Open-Meteo
        try:
            data = await open_meteo_client.get_air_quality(
                latitude=latitude,
                longitude=longitude,
                current=["european_aqi", "pm10", "pm2_5", "carbon_monoxide",
                         "nitrogen_dioxide", "sulphur_dioxide", "ozone"],
            )
            result = open_meteo_client.normalize_air_quality(data, city_id)
            logger.info(f"Open-Meteo 空气质量获取成功: city_id={city_id}")
        except Exception as e:
            logger.warning(f"Open-Meteo 空气质量失败: {e}")

        # 3. 失败时尝试 QWeather
        if not result and location_id:
            try:
                data = await qweather_client.get_air_quality(location_id)
                result = qweather_client.normalize_air_quality(data, city_id)
                logger.info(f"QWeather 空气质量获取成功: city_id={city_id}")
            except Exception as e:
                logger.warning(f"QWeather 空气质量失败: {e}")

        # 4. 写入缓存
        if result:
            import json
            await redis.setex(cache_key, CACHE_TTL_AIR_QUALITY, json.dumps(result, default=str))

        return result

    @staticmethod
    async def get_warning(city_id: int, location_id: str | None = None,
                          city_name: str | None = None) -> list[dict]:
        """
        获取气象灾害预警

        QWeather 有专门的预警接口，Open-Meteo 无此功能。
        LocationID 解析顺序：显式传入 > Redis 缓存映射 > 按城市名在线查询（结果缓存 7 天）
        """
        redis = await get_redis()
        cache_key = f"weather:warning:{city_id}"
        location_map_key = f"weather:qlocation:{city_id}"

        # 1. 查缓存
        import json
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # 2. 确定 QWeather LocationID
        if not location_id:
            location_id = await redis.get(location_map_key)

        if not location_id and city_name:
            try:
                matches = await qweather_client.lookup_city(city_name)
                if matches:
                    location_id = matches[0].get("id")
                    await redis.setex(location_map_key, 7 * 24 * 3600, location_id)
                    logger.info(f"QWeather LocationID 已解析并缓存: {city_name} -> {location_id}")
            except Exception as e:
                logger.warning(f"QWeather 城市查询失败: {city_name}: {e}")

        result = []

        # 3. 尝试 QWeather
        if location_id:
            try:
                data = await qweather_client.get_warning(location_id)
                for item in data:
                    result.append({
                        "city_id": city_id,
                        "warning_id": item.get("id"),
                        "warning_type": item.get("typeName"),
                        "warning_level": item.get("level"),
                        "title": item.get("title") or f"{item.get('typeName')}{item.get('level')}预警",
                        "content": item.get("text"),
                        "publish_time": item.get("pubTime"),
                        "effective": 1,
                        "data_source": "QWeather",
                    })
                logger.info(f"QWeather 预警获取成功: city_id={city_id}, count={len(result)}")
            except Exception as e:
                logger.warning(f"QWeather 预警失败: {e}")
        else:
            logger.debug(f"未提供 QWeather LocationID，跳过预警获取: city_id={city_id}")

        # 3. 写入缓存（即使为空也缓存，避免频繁请求）
        await redis.setex(cache_key, CACHE_TTL_WARNING, json.dumps(result, default=str))

        return result

    @staticmethod
    async def get_life_index(city_id: int, temperature: float = 20,
                             humidity: float = 50, precipitation: float = 0,
                             wind_speed: float = 0, uv: float = 5,
                             location_id: str | None = None) -> list[dict]:
        """
        获取生活指数（多源）

        优先 QWeather（28项指数），失败时本地计算
        """
        redis = await get_redis()
        cache_key = f"weather:life_index:{city_id}"

        # 1. 查缓存
        cached = await redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        result = []

        # 2. 尝试 QWeather（28项专业指数）
        if location_id:
            try:
                data = await qweather_client.get_life_index(location_id, type_=0)
                result = qweather_client.normalize_life_index(data, city_id)
                logger.info(f"QWeather 生活指数获取成功: city_id={city_id}, count={len(result)}")
            except Exception as e:
                logger.warning(f"QWeather 生活指数失败: {e}")

        # 3. QWeather 失败，本地计算
        if not result:
            result = calc_all_life_indices(temperature, humidity, precipitation, wind_speed, uv)
            # 添加 city_id
            for item in result:
                item["city_id"] = city_id
            logger.info(f"本地计算生活指数: city_id={city_id}")

        # 4. 写入缓存
        if result:
            import json
            await redis.setex(cache_key, CACHE_TTL_LIFE_INDEX, json.dumps(result, default=str))

        return result

    @staticmethod
    def get_sunrise_sunset(latitude: float, longitude: float, date: datetime = None) -> dict:
        """
        获取日出日落时间

        基于经纬度计算，无需外部接口
        """
        return calc_sunrise_sunset(latitude, longitude, date)

    @staticmethod
    async def get_historical(
        city_id: int,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """
        获取历史天气数据

        Open-Meteo 历史接口（免费）
        """
        try:
            data = await open_meteo_client.get_historical(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                daily=["weather_code", "temperature_2m_max", "temperature_2m_min",
                       "precipitation_sum", "wind_speed_10m_max"],
            )

            daily = data.get("daily", {})
            dates = daily.get("time", [])

            result = []
            for i, date in enumerate(dates):
                result.append({
                    "city_id": city_id,
                    "date": date,
                    "temp_max": daily.get("temperature_2m_max", [None])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                    "temp_min": daily.get("temperature_2m_min", [None])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                    "precipitation": daily.get("precipitation_sum", [None])[i] if i < len(daily.get("precipitation_sum", [])) else None,
                    "wind_speed_max": daily.get("wind_speed_10m_max", [None])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
                    "data_source": "Open-Meteo",
                })

            logger.info(f"Open-Meteo 历史数据获取成功: city_id={city_id}, days={len(result)}")
            return result
        except Exception as e:
            logger.error(f"Open-Meteo 历史数据失败: {e}")
            return []


# 全局单例
multi_source_weather = MultiSourceWeatherService()
