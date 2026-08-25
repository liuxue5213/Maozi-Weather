from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.city import City, UserCity
from app.models.user import User
from app.schemas.city import CityOut, UserCityAdd, UserCityOut
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
        .where(UserCity.user_id == current_user.id)
        .order_by(UserCity.sort_order)
    )
    return result.scalars().all()


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
    await db.refresh(user_city)
    return user_city


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


@router.get("/all", response_model=list[CityOut])
async def list_all_cities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """获取城市库列表（分页）"""
    result = await db.execute(
        select(City)
        .where(City.is_active == 1)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()
