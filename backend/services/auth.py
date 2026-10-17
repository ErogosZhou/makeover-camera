"""
认证服务
JWT Token 生成与验证
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from config.settings import settings
from models.database import User, get_db


# JWT 配置
SECRET_KEY = settings.IMAGE_GEN_API_KEY or "homeglow-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token 数据"""
    user_id: str
    exp: datetime


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class UserInfo(BaseModel):
    """用户信息响应"""
    id: str
    nickname: str
    avatar_url: Optional[str] = None
    preferred_language: str = "en"
    total_generations: int = 0
    created_at: datetime


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        exp = datetime.fromtimestamp(payload.get("exp"))

        if user_id is None:
            return None

        return TokenData(user_id=user_id, exp=exp)
    except JWTError as e:
        logger.warning(f"Token 验证失败: {e}")
        return None


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    获取当前用户（可选）
    未登录时返回 None，不报错
    """
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials)
    if not token_data:
        return None

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前用户（必须登录）
    未登录时抛出 401 错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def create_or_get_user_by_wechat(
    db: AsyncSession,
    openid: str,
    unionid: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None
) -> User:
    """通过微信创建或获取用户"""
    # 先查找是否存在
    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalar_one_or_none()

    if user:
        # 更新登录时间
        user.last_login_at = datetime.utcnow()
        if nickname:
            user.nickname = nickname
        if avatar_url:
            user.avatar_url = avatar_url
        await db.commit()
        return user

    # 创建新用户
    user = User(
        id=str(uuid.uuid4()),
        wechat_openid=openid,
        wechat_unionid=unionid,
        nickname=nickname or "微信用户",
        avatar_url=avatar_url,
        last_login_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"新用户注册: {user.id} (微信)")
    return user


async def create_or_get_user_by_google(
    db: AsyncSession,
    google_id: str,
    email: Optional[str] = None,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None
) -> User:
    """通过 Google 创建或获取用户"""
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user:
        user.last_login_at = datetime.utcnow()
        if nickname:
            user.nickname = nickname
        if avatar_url:
            user.avatar_url = avatar_url
        await db.commit()
        return user

    # 创建新用户
    user = User(
        id=str(uuid.uuid4()),
        google_id=google_id,
        email=email,
        nickname=nickname or "Google User",
        avatar_url=avatar_url,
        preferred_language="en",
        last_login_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"新用户注册: {user.id} (Google)")
    return user


async def create_guest_user(db: AsyncSession, device_id: str) -> User:
    """创建游客用户（设备绑定）"""
    # 检查是否已有该设备的用户
    # 游客用户暂时不存数据库，只用于本地存储
    # 这里保留接口以便后续升级
    pass
