"""
实况天气快照落库

将多源实况查询结果 upsert 到 weather_realtime 表（每城市保留最新一条）。
供 API 路由与调度器缓存预热共用；落库失败仅记录日志，不影响主流程。
"""
import logging
from datetime import datetime

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.weather import WeatherRealtime

logger = logging.getLogger(__name__)


def _parse_observe_time(raw) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        return datetime.fromisoformat(str(raw).replace("T", " "))
    except ValueError:
        return None


async def persist_realtime_snapshot(payload: dict) -> None:
    """按 city_id upsert 实况快照；任何异常都不向外抛。"""
    city_id = payload.get("city_id")
    if city_id is None:
        return
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WeatherRealtime).where(WeatherRealtime.city_id == city_id)
            )
            row = result.scalar_one_or_none()
            fields = dict(
                station_id=payload.get("station_id"),
                temperature=payload.get("temperature"),
                feels_like=payload.get("feels_like"),
                humidity=payload.get("humidity"),
                pressure=payload.get("pressure"),
                wind_direction=payload.get("wind_direction"),
                wind_speed=payload.get("wind_speed"),
                precipitation=payload.get("precipitation"),
                weather_desc=payload.get("weather_desc"),
                observe_time=_parse_observe_time(payload.get("observe_time")),
                data_source=payload.get("data_source") or "Open-Meteo",
            )
            if row:
                for k, v in fields.items():
                    setattr(row, k, v)
            else:
                db.add(WeatherRealtime(city_id=city_id, **fields))
            await db.commit()
    except Exception as e:
        logger.warning(f"实况快照落库失败 city_id={city_id}: {e}")
