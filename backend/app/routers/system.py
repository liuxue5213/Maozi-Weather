"""
系统级接口

- /stats        首页统计（城市数、同步任务数、历史记录数）
- /cache/clear  清空天气相关 Redis 缓存（管理员）
- /ping-upstream 测试上游数据源连通性
- /config       当前生效的后端配置（敏感值脱敏）
- /users        用户列表与启停用（管理员）
"""
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.city import City, UserCity
from app.models.user import User
from app.models.weather import HistoryObservation, HistorySyncTask
from app.routers.auth import get_current_user

router = APIRouter()


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """首页统计卡片数据"""
    city_count = (await db.execute(select(func.count()).select_from(City))).scalar()
    follow_count = (await db.execute(select(func.count()).select_from(UserCity))).scalar()
    task_count = (
        await db.execute(
            select(func.count()).select_from(HistorySyncTask).where(HistorySyncTask.status.in_(["pending", "running", "failed"]))
        )
    ).scalar()
    history_count = (await db.execute(select(func.count()).select_from(HistoryObservation))).scalar()

    return {
        "cityCount": city_count or 0,
        "followCount": follow_count or 0,
        "syncTasks": task_count or 0,
        "historyRecords": history_count or 0,
    }


@router.post("/cache/clear")
async def clear_weather_cache(
    current_user: User = Depends(get_current_user),
):
    """清空天气前缀的 Redis 缓存"""
    _require_admin(current_user)

    redis = await get_redis()
    deleted = 0
    for prefix in ("weather:",):
        async for key in redis.scan_iter(match=f"{prefix}*"):
            await redis.delete(key)
            deleted += 1
    return {"message": f"已清除 {deleted} 条缓存"}


@router.get("/ping-upstream")
async def ping_upstream(current_user: User = Depends(get_current_user)):
    """测试上游数据源连通性（Open-Meteo）"""
    import httpx

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": 39.9, "longitude": 116.4, "current": "temperature_2m"},
            )
        latency_ms = int((time.monotonic() - started) * 1000)
        if resp.status_code == 200:
            return {"ok": True, "source": "Open-Meteo", "latency_ms": latency_ms}
        return {"ok": False, "source": "Open-Meteo", "latency_ms": latency_ms, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "source": "Open-Meteo", "latency_ms": int((time.monotonic() - started) * 1000), "error": str(e)[:200]}


@router.get("/config")
async def get_runtime_config(current_user: User = Depends(get_current_user)):
    """当前后端运行配置（AppSecret 等敏感信息永不返回明文）"""
    return {
        "app_name": settings.APP_NAME,
        "app_env": settings.APP_ENV,
        "primary_source": settings.WEATHER_PRIMARY_SOURCE,
        "fallback_enabled": settings.WEATHER_FALLBACK_ENABLED,
        "cma_configured": bool(settings.CMA_APPID),
        "qps_limit": settings.CMA_QPS_LIMIT,
        "max_retries": settings.CMA_MAX_RETRIES,
        "qweather_configured": bool(settings.QWEATHER_KEY and settings.QWEATHER_API_HOST),
    }


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户列表（管理员）"""
    _require_admin(current_user)
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at,
            "is_current": u.id == current_user.id,
        }
        for u in users
    ]


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """启用/禁用用户（管理员，不能操作自己）"""
    _require_admin(current_user)
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")

    target.is_active = not target.is_active
    await db.commit()
    return {"id": target.id, "is_active": target.is_active}
