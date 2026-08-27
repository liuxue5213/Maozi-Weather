from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.city import City, UserCity
from app.models.user import User
from app.schemas.city import CityCreate, CityOut, CityUpdate, UserCityAdd, UserCityOut
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/list", response_model=list[UserCityOut])
async def list_user_cities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的关注城市列表"""
    result = await db.execute(
        select(UserCity)
        .options(joinedload(UserCity.city))
        .where(UserCity.user_id == current_user.id)
        .order_by(UserCity.sort_order)
    )
    return result.scalars().unique().all()


@router.post("/add", response_model=UserCityOut)
async def add_city(
    city_data: UserCityAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加关注城市"""
    # 检查城市是否存在
    city_result = await db.execute(select(City).where(City.id == city_data.city_id))
    city = city_result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="城市不存在")

    # 检查是否已关注
    existing = await db.execute(
        select(UserCity).where(
            UserCity.user_id == current_user.id,
            UserCity.city_id == city_data.city_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已关注该城市")

    user_city = UserCity(
        user_id=current_user.id,
        city_id=city_data.city_id,
        view_mode=city_data.view_mode,
    )
    db.add(user_city)
    await db.commit()

    # 重新带出关联的 city（避免 async 懒加载报错）
    result = await db.execute(
        select(UserCity)
        .options(joinedload(UserCity.city))
        .where(UserCity.id == user_city.id)
    )
    return result.scalar_one()


@router.delete("/delete/{user_city_id}")
async def delete_city(
    user_city_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除关注城市"""
    result = await db.execute(
        select(UserCity).where(
            UserCity.id == user_city_id,
            UserCity.user_id == current_user.id,
        )
    )
    user_city = result.scalar_one_or_none()
    if not user_city:
        raise HTTPException(status_code=404, detail="未找到关注记录")

    await db.delete(user_city)
    await db.commit()
    return {"message": "删除成功"}


@router.get("/search", response_model=list[CityOut])
async def search_cities(
    keyword: str = Query(..., min_length=1, max_length=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
):
    """搜索城市"""
    result = await db.execute(
        select(City)
        .where(City.city_name.contains(keyword))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/all")
async def list_all_cities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=2000),
    keyword: str | None = Query(None, max_length=50, description="按城市名过滤"),
):
    """获取城市库列表（分页，带总数，支持按名称过滤）"""
    base = select(City).where(City.is_active == 1)
    if keyword:
        base = base.where(City.city_name.contains(keyword))
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    result = await db.execute(
        base.order_by(City.id).offset((page - 1) * page_size).limit(page_size)
    )
    return {
        "total": total or 0,
        "items": [CityOut.model_validate(c) for c in result.scalars().all()],
    }


# ===== 城市库管理（仅管理员） =====

async def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.post("/manage/create", response_model=CityOut)
async def create_city(
    data: CityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增城市/站点"""
    _require_admin(current_user)

    exists = await db.execute(select(City).where(City.city_name == data.city_name))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同名城市已存在")

    city = City(**data.model_dump())
    db.add(city)
    await db.commit()
    await db.refresh(city)
    return city


@router.put("/manage/{city_id}", response_model=CityOut)
async def update_city(
    city_id: int,
    data: CityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改城市信息"""
    _require_admin(current_user)

    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="城市不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(city, field, value)
    await db.commit()
    await db.refresh(city)
    return city


@router.delete("/manage/{city_id}")
async def delete_city(
    city_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除城市（有关注记录时级联删除关注关系）"""
    _require_admin(current_user)

    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise HTTPException(status_code=404, detail="城市不存在")

    follow_count = (
        await db.execute(
            select(func.count()).select_from(UserCity).where(UserCity.city_id == city_id)
        )
    ).scalar()

    await db.delete(city)
    await db.commit()
    return {"message": f"删除成功（同时移除 {follow_count or 0} 条关注记录）"}
