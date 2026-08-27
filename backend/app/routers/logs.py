"""
监控日志接口

- /api    API 调用日志（api_call_logs 表，由中间件写入）
- /tasks  同步任务近况（history_sync_tasks）
- /cache  Redis 缓存统计（命中率 + 各前缀键数量）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.models.log import ApiCallLog
from app.models.weather import HistorySyncTask
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/api")
async def api_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_code: int | None = Query(None, description="按状态码过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """API 调用日志分页"""
    query = select(ApiCallLog).order_by(ApiCallLog.id.desc())
    if status_code:
        query = query.where(ApiCallLog.status_code == status_code)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = await db.execute(query.offset((page - 1) * page_size).limit(page_size))

    return {
        "total": total or 0,
        "items": [
            {
                "id": log.id,
                "endpoint": log.endpoint,
                "params": log.params,
                "status_code": log.status_code,
                "response_time": log.response_time,
                "created_at": log.created_at,
            }
            for log in items.scalars().all()
        ],
    }


@router.get("/tasks")
async def task_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """同步任务近况"""
    total = (
        await db.execute(select(func.count()).select_from(HistorySyncTask))
    ).scalar()
    result = await db.execute(
        select(HistorySyncTask)
        .order_by(HistorySyncTask.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return {
        "total": total or 0,
        "items": [
            {
                "task_id": t.id,
                "station_id": t.station_id,
                # 映射为前端表格的 event/message 语义
                "event": {
                    "pending": "等待执行",
                    "running": "执行中",
                    "completed": "执行完成",
                    "failed": "执行失败",
                    "stopped": "已停止",
                }.get(t.status, t.status),
                "message": t.error_msg or f"{t.fetched_records}/{t.total_records} 条记录",
                "created_at": t.created_at,
            }
            for t in result.scalars().all()
        ],
    }


@router.get("/cache")
async def cache_stats(current_user: User = Depends(get_current_user)):
    """Redis 缓存命中率与各业务前缀键数量"""
    redis = await get_redis()

    # 命中率来自 Redis 服务端累计统计
    info = await redis.info("stats")
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    hit_rate = round(hits / (hits + misses) * 100, 1) if (hits + misses) else 0.0

    async def count_keys(match: str) -> int:
        return sum(1 async for _ in redis.scan_iter(match=match))

    return {
        "hitRate": hit_rate,
        "realtimeCount": await count_keys("weather:realtime:*"),
        "forecastCount": await count_keys("weather:forecast:*"),
        "warningCount": await count_keys("weather:warning:*"),
    }
