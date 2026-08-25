"""
定时任务调度器

使用 APScheduler 实现：
- 关注城市实况/预报/预警定时拉取缓存
- 历史数据同步任务执行
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


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
    logger.info("开始刷新实况缓存...")
    # TODO: 从数据库获取所有关注城市，逐个调用 weather_service.get_realtime
    pass


async def refresh_forecast_cache():
    """刷新所有关注城市的预报缓存"""
    logger.info("开始刷新预报缓存...")
    # TODO: 从数据库获取所有关注城市，逐个调用 weather_service.get_forecast
    pass


async def refresh_warning_cache():
    """刷新所有关注城市的预警缓存"""
    logger.info("开始刷新预警缓存...")
    # TODO: 从数据库获取所有关注城市，逐个调用 weather_service.get_warning
    pass


async def process_history_tasks():
    """处理待执行的历史同步任务"""
    # TODO: 查询 pending 状态的 HistorySyncTask，启动异步任务执行
    pass
