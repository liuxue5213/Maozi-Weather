"""
公开天气 API（无需登录）

提供完整的天气查询服务，包括：
- 实时天气（含云量、能见度、阵风、露点）
- 逐小时预报（48小时）
- 逐日预报（16天）
- 空气质量（含花粉、气溶胶）
- 生活指数
- 日出日落/月相
"""
import json
import httpx
import time
import logging
from fastapi import APIRouter, Query, HTTPException, Request

from app.core.redis import get_redis
from app.services.air_quality_service import (
    calc_all_life_indices,
    calc_sunrise_sunset,
    calculate_aqi,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ===== 缓存与限流（基于 Redis，支持多实例部署；Redis 不可用时自动降级放行） =====
_CACHE_TTL = 600  # 10 分钟


async def _cache_get(key: str):
    """从 Redis 读取缓存（JSON）。失败则视为未命中。"""
    try:
        raw = await (await get_redis()).get(key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


async def _cache_set(key: str, val, ttl: int = _CACHE_TTL) -> None:
    """写入 Redis 缓存（JSON，带 TTL）。失败则静默跳过。"""
    try:
        await (await get_redis()).set(key, json.dumps(val, ensure_ascii=False), ex=ttl)
    except Exception:
        pass


async def _rate_ok(ip: str, limit: int = 120, window: int = 60) -> bool:
    """基于 Redis 的固定窗口限流（按分钟分桶）。失败则放行。"""
    try:
        r = await get_redis()
        bucket = int(time.time() // window)
        key = f"ratelimit:{ip}:{bucket}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, window)
        return count <= limit
    except Exception:
        return True

# Open-Meteo API
OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
OPEN_METEO_AIR = "https://air-quality-api.open-meteo.com/v1"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"

# WMO 天气代码转中文
WEATHER_CODES = {
    0: "晴", 1: "大部晴朗", 2: "多云", 3: "阴天",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "雪粒",
    80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷暴", 96: "雷暴+小冰雹", 99: "雷暴+大冰雹",
}

# 风向角度转文字
def wind_dir_to_text(deg):
    if deg is None: return None
    dirs = ['北','东北','东','东南','南','西南','西','西北']
    return dirs[round(deg / 45) % 8]


@router.get("/weather")
async def get_weather(
    request: Request,
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
):
    """
    获取完整天气数据（公开接口，无需登录）

    包括：实时天气、逐小时预报、逐日预报、空气质量、生活指数、日出日落

    示例：/weather?latitude=39.9042&longitude=116.4074
    """
    ip = request.client.host if request.client else "unknown"
    if not await _rate_ok(ip):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    cache_key = f"weather:{latitude}:{longitude}"
    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. 获取天气数据（实时+逐小时+逐日）
            resp = await client.get(
                OPEN_METEO_FORECAST,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": ",".join([
                        "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                        "is_day", "precipitation", "rain", "showers", "snowfall",
                        "weather_code", "cloud_cover", "pressure_msl", "surface_pressure",
                        "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
                        "dew_point_2m", "visibility",
                    ]),
                    "hourly": ",".join([
                        "temperature_2m", "relative_humidity_2m", "dew_point_2m",
                        "apparent_temperature", "precipitation_probability", "precipitation",
                        "rain", "showers", "snowfall", "weather_code",
                        "cloud_cover", "visibility", "wind_speed_10m", "wind_direction_10m",
                        "wind_gusts_10m", "uv_index",
                    ]),
                    "daily": ",".join([
                        "weather_code", "temperature_2m_max", "temperature_2m_min",
                        "apparent_temperature_max", "apparent_temperature_min",
                        "sunrise", "sunset", "daylight_duration", "sunshine_duration",
                        "uv_index_max", "precipitation_sum", "rain_sum", "showers_sum",
                        "snowfall_sum", "precipitation_hours", "precipitation_probability_max",
                        "wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant",
                    ]),
                    "timezone": "Asia/Shanghai",
                    "forecast_days": 16,
                    "forecast_hours": 48,
                },
            )
            resp.raise_for_status()
            weather_data = resp.json()

            # 2. 获取空气质量（注意拼上 /air-quality 端点路径）
            air_resp = await client.get(
                f"{OPEN_METEO_AIR}/air-quality",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": ",".join([
                        "european_aqi", "us_aqi", "pm10", "pm2_5",
                        "carbon_monoxide", "nitrogen_dioxide",
                        "sulphur_dioxide", "ozone", "aerosol_optical_depth",
                        "dust", "uv_index",
                    ]),
                    "hourly": ",".join([
                        "european_aqi", "pm10", "pm2_5", "ozone",
                    ]),
                    "timezone": "Asia/Shanghai",
                    "forecast_days": 7,
                },
            )
            if air_resp.status_code == 200:
                air_data = air_resp.json()
            else:
                logger.warning(f"空气质量接口异常: HTTP {air_resp.status_code}")
                air_data = {}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"天气服务暂时不可用: {e}")

    # 解析当前天气
    current = weather_data.get("current", {})
    current_air = air_data.get("current", {})

    # 解析逐小时（只取未来48小时）
    hourly = weather_data.get("hourly", {})
    hourly_times = hourly.get("time", [])[:48]
    hourly_data = []
    for i, t in enumerate(hourly_times):
        hourly_data.append({
            "time": t,
            "temperature": safe_get(hourly.get("temperature_2m", []), i),
            "humidity": safe_get(hourly.get("relative_humidity_2m", []), i),
            "dew_point": safe_get(hourly.get("dew_point_2m", []), i),
            "apparent_temperature": safe_get(hourly.get("apparent_temperature", []), i),
            "weather": WEATHER_CODES.get(safe_get(hourly.get("weather_code", []), i), "未知"),
            "precipitation_probability": safe_get(hourly.get("precipitation_probability", []), i),
            "precipitation": safe_get(hourly.get("precipitation", []), i),
            "cloud_cover": safe_get(hourly.get("cloud_cover", []), i),
            "visibility": safe_get(hourly.get("visibility", []), i),
            "wind_speed": safe_get(hourly.get("wind_speed_10m", []), i),
            "wind_direction": wind_dir_to_text(safe_get(hourly.get("wind_direction_10m", []), i)),
            "wind_gusts": safe_get(hourly.get("wind_gusts_10m", []), i),
            "uv_index": safe_get(hourly.get("uv_index", []), i),
        })

    # 解析逐日
    daily = weather_data.get("daily", {})
    daily_data = []
    for i in range(len(daily.get("time", []))):
        daily_data.append({
            "date": safe_get(daily.get("time", []), i),
            "weather": WEATHER_CODES.get(safe_get(daily.get("weather_code", []), i), "未知"),
            "temp_max": safe_get(daily.get("temperature_2m_max", []), i),
            "temp_min": safe_get(daily.get("temperature_2m_min", []), i),
            "apparent_max": safe_get(daily.get("apparent_temperature_max", []), i),
            "apparent_min": safe_get(daily.get("apparent_temperature_min", []), i),
            "precipitation_sum": safe_get(daily.get("precipitation_sum", []), i),
            "precipitation_hours": safe_get(daily.get("precipitation_hours", []), i),
            "precipitation_probability": safe_get(daily.get("precipitation_probability_max", []), i),
            "wind_speed_max": safe_get(daily.get("wind_speed_10m_max", []), i),
            "wind_gusts_max": safe_get(daily.get("wind_gusts_10m_max", []), i),
            "wind_direction": wind_dir_to_text(safe_get(daily.get("wind_direction_10m_dominant", []), i)),
            "uv_index_max": safe_get(daily.get("uv_index_max", []), i),
            "sunrise": safe_get(daily.get("sunrise", []), i),
            "sunset": safe_get(daily.get("sunset", []), i),
            "daylight_duration": safe_get(daily.get("daylight_duration", []), i),
            "sunshine_duration": safe_get(daily.get("sunshine_duration", []), i),
        })

    # 计算生活指数
    temp = current.get("temperature_2m", 20)
    humidity = current.get("relative_humidity_2m", 50)
    precip = current.get("precipitation", 0)
    wind = current.get("wind_speed_10m", 0)
    uv = current.get("uv_index", 5)
    life_indices = calc_all_life_indices(temp, humidity, precip, wind, uv)

    # AQI 等级（国标 GB 3095-2012，由污染物浓度换算）
    co = current_air.get("carbon_monoxide")
    co = co / 1000.0 if co is not None else None
    cn = calculate_aqi(
        pm25=current_air.get("pm2_5"),
        pm10=current_air.get("pm10"),
        so2=current_air.get("sulphur_dioxide"),
        no2=current_air.get("nitrogen_dioxide"),
        co=co,
        o3=current_air.get("ozone"),
    )
    aqi = cn["aqi"]
    aqi_level = cn["level"]
    aqi_primary = cn["primary"]

    result = {
        "latitude": latitude,
        "longitude": longitude,
        "current": {
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "dew_point": current.get("dew_point_2m"),
            "pressure_msl": current.get("pressure_msl"),
            "pressure_surface": current.get("surface_pressure"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": wind_dir_to_text(current.get("wind_direction_10m")),
            "wind_gusts": current.get("wind_gusts_10m"),
            "precipitation": current.get("precipitation"),
            "rain": current.get("rain"),
            "showers": current.get("showers"),
            "snowfall": current.get("snowfall"),
            "cloud_cover": current.get("cloud_cover"),
            "visibility": current.get("visibility"),
            "is_day": current.get("is_day"),
            "uv_index": current.get("uv_index"),
            "weather": WEATHER_CODES.get(current.get("weather_code", 0), "未知"),
        },
        "air_quality": {
            "aqi": aqi,
            "aqi_level": aqi_level,
            "aqi_primary": aqi_primary,
            "us_aqi": current_air.get("us_aqi"),
            "pm25": current_air.get("pm2_5"),
            "pm10": current_air.get("pm10"),
            "co": current_air.get("carbon_monoxide"),
            "no2": current_air.get("nitrogen_dioxide"),
            "so2": current_air.get("sulphur_dioxide"),
            "o3": current_air.get("ozone"),
            "aerosol": current_air.get("aerosol_optical_depth"),
            "dust": current_air.get("dust"),
            "uv_index": current_air.get("uv_index"),
        },
        "hourly": hourly_data,
        "daily": daily_data,
        "life_indices": life_indices,
    }

    await _cache_set(cache_key, result)
    return result


@router.get("/search/city")
async def search_city(
    request: Request,
    name: str = Query(..., description="城市名称"),
):
    """
    搜索城市（公开接口，无需登录）

    示例：/search/city?name=北京
    """
    ip = request.client.host if request.client else "unknown"
    if not await _rate_ok(ip, limit=60, window=60):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    cache_key = f"city:{name}"
    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": name, "count": 10, "language": "zh", "format": "json"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"搜索服务暂时不可用: {e}")

    results = []
    for item in data.get("results", []):
        results.append({
            "name": item.get("name"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "country": item.get("country"),
            "admin1": item.get("admin1"),
        })

    result = {"results": results}
    await _cache_set(cache_key, result)
    return result


@router.get("/life-index")
async def get_life_index(
    temperature: float = Query(20.0, description="当前温度"),
    humidity: float = Query(50.0, description="当前湿度"),
    precipitation: float = Query(0.0, description="降水量"),
    wind_speed: float = Query(0.0, description="风速"),
    uv: float = Query(5.0, description="紫外线指数"),
):
    """
    获取生活指数（公开接口，无需登录）
    """
    indices = calc_all_life_indices(temperature, humidity, precipitation, wind_speed, uv)
    return {"indices": indices}


def safe_get(lst, idx):
    """安全获取列表元素"""
    try:
        return lst[idx]
    except (IndexError, TypeError):
        return None
