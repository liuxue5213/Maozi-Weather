"""
历史数据同步服务

负责执行历史气象数据的同步任务
"""
import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.city import City
from app.models.weather import HistoryObservation, HistorySyncTask
from app.utils.open_meteo_client import open_meteo_client

logger = logging.getLogger(__name__)


async def execute_sync_task(task_id: int):
    """
    执行历史数据同步任务

    从 Open-Meteo 历史接口拉取数据并写入数据库
    """
    async with AsyncSessionLocal() as db:
        # 获取任务
        result = await db.execute(
            select(HistorySyncTask).where(HistorySyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task or task.status == "completed":
            logger.warning(f"任务不存在或已完成: {task_id}")
            return

        # 更新状态为执行中
        task.status = "running"
        task.error_msg = None
        await db.commit()

        try:
            # 获取站点经纬度（从城市库查询）
            lat, lon = await _get_station_coords(db, task.station_id)

            # 解析日期范围
            start_date = datetime.strptime(task.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(task.end_date, "%Y-%m-%d")

            # 计算总天数
            total_days = (end_date - start_date).days + 1
            task.total_records = total_days
            task.fetched_records = 0
            await db.commit()

            # 每次最多拉取 90 天（避免请求过大）
            chunk_size = 90
            fetched = 0

            current_start = start_date
            while current_start <= end_date:
                current_end = min(current_start + timedelta(days=chunk_size - 1), end_date)

                logger.info(f"拉取 {task.station_id}: {current_start.date()} ~ {current_end.date()}")

                data = await open_meteo_client.get_historical(
                    latitude=lat,
                    longitude=lon,
                    start_date=current_start.strftime("%Y-%m-%d"),
                    end_date=current_end.strftime("%Y-%m-%d"),
                    daily=[
                        "weather_code",
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_sum",
                        "wind_speed_10m_max",
                    ],
                )

                # 解析并写入数据库
                daily = data.get("daily", {})
                dates = daily.get("time", [])

                for i, date_str in enumerate(dates):
                    # 检查是否已存在
                    existing = await db.execute(
                        select(HistoryObservation).where(
                            HistoryObservation.station_id == task.station_id,
                            HistoryObservation.observe_time == f"{date_str} 00:00:00",
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # 创建记录
                    obs = HistoryObservation(
                        station_id = task.station_id,
                        observe_time=f"{date_str} 00:00:00",
                        temperature=daily.get("temperature_2m_max", [None])[i]
                        if i < len(daily.get("temperature_2m_max", []))
                        else None,
                        wind_speed=daily.get("wind_speed_10m_max", [None])[i]
                        if i < len(daily.get("wind_speed_10m_max", []))
                        else None,
                        precipitation=daily.get("precipitation_sum", [None])[i]
                        if i < len(daily.get("precipitation_sum", []))
                        else None,
                        data_source="Open-Meteo",
                    )
                    db.add(obs)
                    fetched += 1

                # 更新进度
                task.fetched_records = fetched
                await db.commit()

                # 移动到下一个时间段
                current_start = current_end + timedelta(days=1)

                # 限速：避免请求过快
                await asyncio.sleep(1)

            # 完成
            task.status = "completed"
            task.fetched_records = fetched
            task.completed_at = datetime.now()
            await db.commit()

            logger.info(f"同步任务完成: {task_id}, 共拉取 {fetched} 条记录")

        except Exception as e:
            logger.error(f"同步任务失败: {task_id}, 错误: {e}")
            task.status = "failed"
            task.error_msg = str(e)
            await db.commit()


async def _get_station_coords(db, station_id: str) -> tuple[float, float]:
    """
    根据站点ID获取经纬度

    优先从城市库查询，找不到则使用默认坐标
    """
    # 从城市库查询
    result = await db.execute(
        select(City).where(City.station_id == station_id)
    )
    city = result.scalar_one_or_none()

    if city and city.latitude and city.longitude:
        return (city.latitude, city.longitude)

    # 默认返回北京坐标
    logger.warning(f"未找到站点 {station_id} 的坐标，使用默认值")
    return (39.9042, 116.4074)
