"""
CMA 中国气象数据网 API 客户端

封装对 data.cma.cn 接口的调用，包含：
- appid/appsecret 鉴权
- 令牌桶限流（QPS 控制）
- 自动重试
- 缺测数据处理
- 异常捕获
"""

import asyncio
import logging
from datetime import datetime, timedelta

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class CMARateLimiter:
    """令牌桶限流器"""

    def __init__(self, rate: int = 10):
        self.rate = rate  # 每秒请求数
        self.tokens = rate
        self.last_refill = datetime.now()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """获取令牌，无令牌则等待"""
        async with self._lock:
            now = datetime.now()
            elapsed = (now - self.last_refill).total_seconds()
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class CMAClient:
    """CMA 气象数据网 API 客户端"""

    def __init__(self):
        self.base_url = settings.CMA_BASE_URL
        self.appid = settings.CMA_APPID
        self.appsecret = settings.CMA_APPSECRET
        self.max_retries = settings.CMA_MAX_RETRIES
        self.retry_delay = settings.CMA_RETRY_DELAY
        self.rate_limiter = CMARateLimiter(rate=settings.CMA_QPS_LIMIT)
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                headers={
                    "User-Agent": "MaoZi-Weather/0.1.0",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def close(self):
        """关闭连接"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _build_auth_params(self) -> dict:
        """构建鉴权参数"""
        return {
            "appid": self.appid,
            "appsecret": self.appsecret,
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        **kwargs,
    ) -> dict:
        """
        通用请求方法（带限流、重试、异常处理）

        Args:
            method: HTTP 方法
            endpoint: API 端点（相对路径）
            params: 查询参数

        Returns:
            API 响应数据

        Raises:
            CMAAPIError: API 调用失败
        """
        if params is None:
            params = {}
        params.update(self._build_auth_params())

        client = await self.get_client()
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            # 限流
            await self.rate_limiter.acquire()

            try:
                logger.debug(f"CMA 请求 [{attempt}/{self.max_retries}]: {endpoint} params={params}")

                response = await client.request(method, endpoint, params=params, **kwargs)

                # 429 限流处理
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.retry_delay * attempt))
                    logger.warning(f"CMA 限流 429，等待 {retry_after}s 后重试")
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                # 检查业务错误码
                if isinstance(data, dict) and data.get("code") not in (None, 200, "200", 0):
                    raise CMAAPIError(
                        code=data.get("code"),
                        message=data.get("msg", "未知错误"),
                    )

                return data

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"CMA 请求超时 [{attempt}/{self.max_retries}]: {endpoint}")
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.warning(f"CMA HTTP 错误 [{attempt}/{self.max_retries}]: {e.response.status_code}")
            except CMAAPIError:
                raise
            except Exception as e:
                last_exception = e
                logger.error(f"CMA 请求异常 [{attempt}/{self.max_retries}]: {e}")

            # 重试等待
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * attempt)

        raise CMAAPIError(code=-1, message=f"请求失败，已重试 {self.max_retries} 次: {last_exception}")

    # ===== 业务接口封装 =====

    async def get_realtime(self, station_id: str) -> dict:
        """获取实况天气"""
        return await self.request("GET", "/weather/realtime", params={"stationid": station_id})

    async def get_forecast(self, city_code: str) -> dict:
        """获取天气预报"""
        return await self.request("GET", "/weather/forecast", params={"citycode": city_code})

    async def get_warning(self, city_code: str) -> dict:
        """获取气象预警"""
        return await self.request("GET", "/weather/warning", params={"citycode": city_code})

    async def get_history(
        self,
        station_id: str,
        start_time: str,
        end_time: str,
        page: int = 1,
        page_size: int = 500,
    ) -> dict:
        """
        获取历史观测数据

        Args:
            station_id: 站点ID
            start_time: 开始时间 YYYY-MM-DD HH:MM:SS
            end_time: 结束时间 YYYY-MM-DD HH:MM:SS
            page: 页码
            page_size: 每页条数
        """
        return await self.request(
            "GET",
            "/weather/history",
            params={
                "stationid": station_id,
                "starttime": start_time,
                "endtime": end_time,
                "page": page,
                "pagesize": page_size,
            },
        )


class CMAAPIError(Exception):
    """CMA API 异常"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"CMA API Error [{code}]: {message}")


# 全局单例
cma_client = CMAClient()
