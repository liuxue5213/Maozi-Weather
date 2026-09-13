from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, verify_password, get_password_hash
from app.models.city import City, UserCity
from app.models.user import User
from app.schemas.user import Token, UserLogin, UserOut

router = APIRouter()
security = HTTPBearer()

GUEST_USERNAME = "guest"
# 无法定位时的兜底默认城市（按 city_name 模糊匹配）
GUEST_FALLBACK_CITIES = ["北京"]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT token 解析当前用户"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌内容无效",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/logout")
async def logout():
    """登出（前端清除 token 即可）"""
    return {"message": "登出成功"}


@router.post("/guest", response_model=Token)
async def guest_login(
    db: AsyncSession = Depends(get_db),
    latitude: float | None = Query(None, description="设备纬度，用于自动选择最近城市"),
    longitude: float | None = Query(None, description="设备经度"),
):
    """游客登录（App 默认免登录入口）。

    首次调用自动创建 guest 账号；携带经纬度时自动关注离定位最近的城市，
    无法定位时兜底关注默认城市。账号已有关注城市则不再重复预置。
    """
    result = await db.execute(select(User).where(User.username == GUEST_USERNAME))
    user = result.scalar_one_or_none()

    created = False
    if not user:
        import secrets

        user = User(
            username=GUEST_USERNAME,
            password_hash=get_password_hash(secrets.token_urlsafe(24)),
            real_name="游客",
            is_admin=0,
            is_active=1,
        )
        db.add(user)
        await db.flush()
        created = True

    # 无关注城市时按定位预置默认城市（新建账号或被清空的账号都适用）
    cities_result = await db.execute(
        select(func.count()).select_from(UserCity).where(UserCity.user_id == user.id)
    )
    if (cities_result.scalar() or 0) == 0:
        for city_id in await _pick_default_city_ids(db, latitude, longitude):
            db.add(UserCity(user_id=user.id, city_id=city_id, sort_order=0))

    if created or db.new or db.dirty:
        await db.commit()
    await db.refresh(user)

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, user=UserOut.model_validate(user))


async def _pick_default_city_ids(
    db: AsyncSession, latitude: float | None, longitude: float | None
) -> list[int]:
    """按定位选择最近的城市；无定位或城市库为空时返回兜底城市。"""
    all_cities = (await db.execute(select(City))).scalars().all()

    if latitude is not None and longitude is not None and all_cities:
        def distance(city: City) -> float:
            if city.latitude is None or city.longitude is None:
                return float("inf")
            # 粗略欧氏距离即可满足"最近城市"的挑选目的
            return (city.latitude - latitude) ** 2 + (city.longitude - longitude) ** 2

        nearest = min(all_cities, key=distance)
        if nearest.id is not None:
            return [nearest.id]

    for name in GUEST_FALLBACK_CITIES:
        for city in all_cities:
            if name in (city.city_name or ""):
                return [city.id]
    return []


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户信息"""
    return UserOut.model_validate(current_user)
