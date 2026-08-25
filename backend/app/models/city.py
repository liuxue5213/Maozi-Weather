from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class City(Base):
    """城市/站点库"""
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    city_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    city_code: Mapped[str | None] = mapped_column(String(20), index=True)  # 行政区划代码
    station_id: Mapped[str | None] = mapped_column(String(20), index=True)  # 气象站点ID
    province: Mapped[str | None] = mapped_column(String(50))
    longitude: Mapped[float | None] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关联
    user_cities: Mapped[list["UserCity"]] = relationship(back_populates="city")


class UserCity(Base):
    """用户关注城市"""
    __tablename__ = "user_cities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    city_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cities.id", ondelete="CASCADE"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    view_mode: Mapped[str] = mapped_column(String(10), default="city")  # city | station
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关联
    city: Mapped["City"] = relationship(back_populates="user_cities")
