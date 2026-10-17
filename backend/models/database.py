"""
数据库模型定义
使用 SQLAlchemy 2.0 异步模式
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config.settings import settings


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 基础信息
    nickname: Mapped[str] = mapped_column(String(50), default="换装相机 User")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 第三方绑定
    wechat_openid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    wechat_unionid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    apple_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)

    # 偏好设置
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    preferred_styles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 字符串
    default_budget: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # 统计
    total_generations: Mapped[int] = mapped_column(Integer, default=0)
    total_saved_items: Mapped[int] = mapped_column(Integer, default=0)

    # 关系
    history_records: Mapped[List["HistoryRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class HistoryRecord(Base):
    """历史记录表"""
    __tablename__ = "history_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 游客设备标识
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 输入
    original_image_url: Mapped[str] = mapped_column(String(500))
    room_type: Mapped[str] = mapped_column(String(50))
    style: Mapped[str] = mapped_column(String(50))
    budget: Mapped[str] = mapped_column(String(20))

    # 输出
    generated_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shopping_list: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 字符串
    total_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 状态
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关系
    user: Mapped[Optional["User"]] = relationship(back_populates="history_records")


# 数据库引擎和会话
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """获取数据库会话（用于依赖注入）"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
