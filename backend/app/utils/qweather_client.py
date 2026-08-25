"""
和风天气 (QWeather) API 客户端

国内最全面的天气数据
- 使用 Ed25519 JWT 认证
- 自定义 API Host
- 支持实况、预报、生活指数、城市搜索等

官网: https://dev.qweather.com
文档: https://dev.qweather.com/docs/api/
"""

import logging
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class QWeatherClient:
    """和风天气 API 客户端"""

    def __init__(self):
        # 使用自定义 API Host（从控制台获取）
        self.api_host = settings.QWEATHER_API_HOST
        self.base_url = f"https://{self.api_host}"
        self.api_key = settings.QWEATHER_KEY
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

    async def _request(self, endpoint: str, params: dict) -> dict:
        """通用请求方法（JWT 认证）"""
        if not self.api_key:
            raise QWeatherError("未配置和风天气 API Key")

        # 创建 JWT token
        import jwt
        import time
        from pathlib import Path

        private_key_path = Path(settings.QWEATHER_PRIVATE_KEY_PATH)
        private_key = private_key_path.read_text()

        now = int(time.time())
        payload = {
            'sub': settings.QWEATHER_USER_ID,
            'iat': now,
            'exp': now + 3600,
        }
        headers = {'kid': settings.QWEATHER_CRED_ID}
        token = jwt.encode(payload, private_key, algorithm='EdDSA', headers=headers)

        client = await self.get_client()
        url = f"{self.base_url}/{endpoint}"
        auth_headers = {'Authorization': f'Bearer {token}'}

        logger.debug(f"和风天气请求: {endpoint} params={params}")

        response = await client.get(url, params=params, headers=auth_headers)
        response.raise_for_status()
        data = response.json()

        # 检查和风天气错误码
        if data.get("code") not in ("200", 200, None):
            raise QWeatherError(code=data.get("code"), message=data.get("message", "未知错误"))

        return data

    # ===== 城市查询 =====

    async def lookup_city(self, location: str, adm: str | None = None, range_: str = "cn") -> list[dict]:
        """
        城市查询

        Args:
            location: 城市名/地名/经纬度/LocationID
            adm: 行政区划（省/市）
            range_: 范围（cn-国内，world-全球）
        """
        params = {"location": location, "range": range_}
        if adm:
            params["adm"] = adm

        data = await self._request("geo/v2/city/lookup", params)
        return data.get("location", [])

    # ===== 天气数据 =====

    async def get_realtime_weather(self, location_id: str) -> dict:
        """获取实时天气"""
        data = await self._request("v7/weather/now", {"location": location_id})
        return data.get("now", {})

    async def get_daily_forecast(self, location_id: str, days: int = 15) -> list[dict]:
        """
        获取逐日预报

        Args:
            location_id: 城市 LocationID
            days: 天数（3/7/10/15/30）
        """
        days_map = {3: "3d", 7: "7d", 10: "10d", 15: "15d", 30: "30d"}
        endpoint = f"v7/weather/{days_map.get(days, '15d')}"

        data = await self._request(endpoint, {"location": location_id})
        return data.get("daily", [])

    async def get_hourly_forecast(self, location_id: str, hours: int = 24) -> list[dict]:
        """
        获取逐小时预报

        Args:
            location_id: 城市 LocationID
            hours: 小时数（24/72/168）
        """
        hours_map = {24: "24h", 72: "72h", 168: "168h"}
        endpoint = f"v7/weather/{hours_map.get(hours, '24h')}"

        data = await self._request(endpoint, {"location": location_id})
        return data.get("hourly", [])

    # ===== 生活指数 =====

    async def get_life_index(self, location_id: str, type_: int = 0) -> list[dict]:
        """
        获取生活指数

        Args:
            location_id: 城市 LocationID
            type_: 指数类型（0-全部，1-穿衣，2-紫外线，3-洗车，4-运动等）
        """
        data = await self._request("v7/indices/1d", {
            "location": location_id,
            "type": type_,
        })
        return data.get("daily", [])

    # ===== 日出日落 =====

    async def get_sunrise_sunset(self, location_id: str, date: str | None = None) -> dict:
        """
        获取日出日落

        Args:
            location_id: 城市 LocationID
            date: 日期 YYYYMMDD（默认今天）
        """
        if not date:
            date = datetime.now().strftime("%Y%m%d")

        data = await self._request("v7/astronomy/sun", {
            "location": location_id,
            "date": date,
        })
        return data

    # ===== 数据标准化 =====

    @staticmethod
    def normalize_realtime(data: dict, city_id: int) -> dict | None:
        """标准化实时天气"""
        if not data:
            return None

        return {
            "city_id": city_id,
            "temperature": data.get("temp"),
            "feels_like": data.get("feelsLike"),
            "humidity": data.get("humidity"),
            "pressure": data.get("pressure"),
            "wind_direction": data.get("windDir"),
            "wind_speed": data.get("windSpeed"),
            "precipitation": data.get("precip"),
            "weather_desc": data.get("text"),
            "observe_time": data.get("obsTime"),
            "data_source": "QWeather",
        }

    @staticmethod
    def normalize_daily_forecast(data: list[dict], city_id: int) -> list[dict]:
        """标准化逐日预报"""
        result = []
        for item in data:
            result.append({
                "city_id": city_id,
                "forecast_type": "daily",
                "forecast_time": f"{item.get('fxDate', '')}T00:00:00",
                "temp_max": item.get("tempMax"),
                "temp_min": item.get("tempMin"),
                "weather_desc_day": item.get("textDay"),
                "weather_desc_night": item.get("textNight"),
                "precipitation": item.get("precip"),
                "wind_speed": item.get("windSpeedDay"),
                "sunrise": item.get("sunrise"),
                "sunset": item.get("sunset"),
                "data_source": "QWeather",
            })
        return result

    @staticmethod
    def normalize_hourly_forecast(data: list[dict], city_id: int) -> list[dict]:
        """标准化逐小时预报"""
        result = []
        for item in data:
            result.append({
                "city_id": city_id,
                "forecast_type": "hourly",
                "forecast_time": item.get("fxTime", ""),
                "temperature": item.get("temp"),
                "humidity": item.get("humidity"),
                "weather_desc": item.get("text"),
                "wind_speed": item.get("windSpeed"),
                "wind_direction": item.get("windDir"),
                "precipitation": item.get("precip"),
                "pop": item.get("pop"),
                "data_source": "QWeather",
            })
        return result

    @staticmethod
    def normalize_life_index(data: list[dict], city_id: int) -> list[dict]:
        """标准化生活指数"""
        type_map = {
            "1": "穿衣指数", "2": "紫外线指数", "3": "洗车指数",
            "4": "运动指数", "5": "污染扩散条件指数", "6": "交通指数",
            "7": "化妆指数", "8": "晾晒指数", "9": "旅游指数",
            "10": "钓鱼指数", "11": "过敏指数", "12": "舒适度指数",
        }

        result = []
        for item in data:
            index_type = str(item.get("type", ""))
            result.append({
                "city_id": city_id,
                "index_type": index_type,
                "index_name": type_map.get(index_type, item.get("name", "未知")),
                "index_level": item.get("level"),
                "index_desc": item.get("text"),
                "data_source": "QWeather",
            })
        return result


class QWeatherError(Exception):
    """和风天气 API 异常"""

    def __init__(self, code: str | None = None, message: str = ""):
        self.code = code
        self.message = message
        super().__init__(f"QWeather Error [{code}]: {message}")


# 全局单例
qweather_client = QWeatherClient()
