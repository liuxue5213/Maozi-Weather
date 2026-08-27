from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.weather import HistoryObservation, HistorySyncTask
from app.routers.auth import get_current_user
from app.schemas.weather import (
    HistoryObservationOut,
    HistorySyncTaskCreate,
    HistorySyncTaskOut,
)

router = APIRouter()


# ===== 同步任务管理（仅管理员） =====

@router.post("/task/create", response_model=HistorySyncTaskCreate)
async def create_sync_task(
    task_data: HistorySyncTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建历史同步任务（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    task = HistorySyncTask(
        station_id=task_data.station_id,
        start_date=task_data.start_date,
        end_date=task_data.end_date,
        status="pending",
        created_by=current_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 由调度器每分钟扫描 pending 任务并执行（见 services/scheduler.py）
    return task


@router.get("/task/list")
async def list_sync_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取同步任务列表和进度"""
    query = select(HistorySyncTask).order_by(HistorySyncTask.created_at.desc())
    if status_filter:
        query = query.where(HistorySyncTask.status == status_filter)

    total = await db.execute(select(func.count()).select_from(query.subquery()))
    items = await db.execute(query.offset((page - 1) * page_size).limit(page_size))

    return {
        "total": total.scalar(),
        "page": page,
        "page_size": page_size,
        "items": items.scalars().all(),
    }


@router.post("/task/{task_id}/retry")
async def retry_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重试失败的任务"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    result = await db.execute(
        select(HistorySyncTask).where(HistorySyncTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = "pending"
    task.error_msg = None
    await db.commit()

    # 已置回 pending，等待调度器重新领取执行
    return {"message": "任务已重新提交"}


@router.post("/task/{task_id}/stop")
async def stop_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """停止执行中的任务"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    result = await db.execute(
        select(HistorySyncTask).where(HistorySyncTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = "stopped"
    await db.commit()
    return {"message": "任务已停止"}


# ===== 历史数据查询 =====

@router.get("/query", response_model=list[HistoryObservationOut])
async def query_history(
    station_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
):
    """查询本地库历史观测数据"""
    result = await db.execute(
        select(HistoryObservation)
        .where(
            HistoryObservation.station_id == station_id,
            HistoryObservation.observe_time >= start_time,
            HistoryObservation.observe_time <= end_time,
        )
        .order_by(HistoryObservation.observe_time)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()


@router.get("/export")
async def export_history(
    station_id: str = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出 CSV 历史数据（Web）"""
    import csv
    import io

    result = await db.execute(
        select(HistoryObservation)
        .where(
            HistoryObservation.station_id == station_id,
            HistoryObservation.observe_time >= start_time,
            HistoryObservation.observe_time <= end_time,
        )
        .order_by(HistoryObservation.observe_time)
    )
    observations = result.scalars().all()

    # 生成 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "站点ID", "观测时间", "温度(℃)", "气压(hPa)", "湿度(%)",
        "风向(°)", "风速(m/s)", "降水(mm)", "是否缺测", "缺测字段",
    ])

    for obs in observations:
        writer.writerow([
            obs.station_id,
            obs.observe_time.strftime("%Y-%m-%d %H:%M:%S") if obs.observe_time else "",
            obs.temperature,
            obs.pressure,
            obs.humidity,
            obs.wind_direction,
            obs.wind_speed,
            obs.precipitation,
            obs.is_missing,
            obs.missing_fields,
        ])

    output.seek(0)
    filename = f"history_{station_id}_{start_time.date()}_{end_time.date()}.csv"

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
