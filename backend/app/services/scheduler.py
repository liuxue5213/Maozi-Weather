"""
定时任务调度器

使用 APScheduler 实现：
- 关注城市实况/预报/预警定时拉取缓存
- 历史数据同步任务执行
"""

import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, or_

from app.core.database import AsyncSessionLocal
from app.models.city import City, UserCity
from app.models.weather import HistorySyncTask
from app.services.history_sync import execute_sync_task
from app.services.multi_source_weather import multi_source_weather
from app.core.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# 防止同一任务并发重入（避免长任务被重复触发）
_locks = {
    "realtime": asyncio.Lock(),
    "forecast": asyncio.Lock(),
    "warning": asyncio.Lock(),
}


async def _followed_cities() -> list[dict]:
    """获取有关注用户的城市坐标（去重）"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(City.id, City.city_name, City.latitude, City.longitude)
            .join(UserCity, UserCity.city_id == City.id)
            .where(
                City.latitude.isnot(None),
                City.longitude.isnot(None),
                City.is_active == 1,
            )
            .distinct()
        )
        return [
            {"city_id": r[0], "city_name": r[1], "latitude": float(r[2]), "longitude": float(r[3])}
            for r in result.all()
        ]


async def init_scheduler():
    """初始化并启动调度器"""
    # 定时拉取关注城市实时天气（每 10 分钟）
    scheduler.add_job(
        refresh_realtime_cache,
        IntervalTrigger(minutes=10),
        id="refresh_realtime",
        name="刷新实况缓存",
        replace_existing=True,
    )

    # 定时拉取预报（每 1 小时）
    scheduler.add_job(
        refresh_forecast_cache,
        IntervalTrigger(hours=1),
        id="refresh_forecast",
        name="刷新预报缓存",
        replace_existing=True,
    )

    # 定时拉取预警（每 5 分钟）
    scheduler.add_job(
        refresh_warning_cache,
        IntervalTrigger(minutes=5),
        id="refresh_warning",
        name="刷新预警缓存",
        replace_existing=True,
    )

    # 检查并执行待处理的历史同步任务
    scheduler.add_job(
        process_history_tasks,
        IntervalTrigger(minutes=1),
        id="process_history",
        name="处理历史同步任务",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("定时任务调度器已启动")


async def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")


async def refresh_realtime_cache():
    """刷新所有关注城市的实况缓存"""
    if _locks["realtime"].locked():
        return
    async with _locks["realtime"]:
        logger.info("开始刷新实况缓存...")
        for c in await _followed_cities():
            try:
                await multi_source_weather.get_realtime(c["city_id"], c["latitude"], c["longitude"])
            except Exception as e:
                logger.warning(f"实况缓存刷新失败 city={c['city_id']}: {e}")


async def refresh_forecast_cache():
    """刷新所有关注城市的预报缓存"""
    if _locks["forecast"].locked():
        return
    async with _locks["forecast"]:
        logger.info("开始刷新预报缓存...")
        for c in await _followed_cities():
            try:
                await multi_source_weather.get_forecast(c["city_id"], c["latitude"], c["longitude"])
            except Exception as e:
                logger.warning(f"预报缓存刷新失败 city={c['city_id']}: {e}")


async def refresh_warning_cache():
    """刷新所有关注城市的预警缓存（依赖和风天气 LocationID）"""
    # 预警需要 QWeather 的 LocationID，未配置 QWeather 时不拉取
    if not settings.QWEATHER_API_HOST:
        return
    if _locks["warning"].locked():
        return
    async with _locks["warning"]:
        logger.info("开始刷新预警缓存...")
        for c in await _followed_cities():
            try:
                await multi_source_weather.get_warning(c["city_id"], city_name=c["city_name"])
            except Exception as e:
                logger.warning(f"预警缓存刷新失败 city={c['city_id']}: {e}")


async def process_history_tasks():
    """处理待执行的历史同步任务（带退避与并发锁）"""
    # 失败任务 5 分钟退避，避免无限高频重试；running 任务不重复选取；
    # 卡死的 running 任务超过 30 分钟视为僵死，交还队列重跑
    cutoff = datetime.now() - timedelta(minutes=5)
    stale_running_cutoff = datetime.now() - timedelta(minutes=30)
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(HistorySyncTask).where(
                    or_(
                        HistorySyncTask.status == "pending",
                        (HistorySyncTask.status == "failed") & (HistorySyncTask.updated_at < cutoff),
                        (HistorySyncTask.status == "running") & (HistorySyncTask.updated_at < stale_running_cutoff),
                    )
                ).order_by(HistorySyncTask.created_at).limit(1)
            )
            task = result.scalar_one_or_none()

            if task:
                # 先置 running 再异步执行，防止调度器重复选取同一任务
                task.status = "running"
                task.error_msg = None
                await db.commit()
                logger.info(f"开始执行同步任务: {task.id}, 站点: {task.station_id}")
                asyncio.create_task(execute_sync_task(task.id))
    except Exception as e:
        logger.error(f"处理历史同步任务出错: {e}")
