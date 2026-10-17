"""
认证相关 API 路由
"""
import httpx
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.database import User, get_db
from services.auth import (
    create_access_token,
    create_or_get_user_by_wechat,
    create_or_get_user_by_google,
    get_current_user,
    get_current_user_optional,
    TokenResponse,
    UserInfo,
    ACCESS_TOKEN_EXPIRE_DAYS
)
from config.settings import settings


router = APIRouter(prefix="/auth", tags=["认证"])


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str  # 微信授权码


class GoogleLoginRequest(BaseModel):
    """Google 登录请求"""
    id_token: str  # Google ID Token


class UpdateProfileRequest(BaseModel):
    """更新用户信息请求"""
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: Optional[str] = None
    default_budget: Optional[str] = None


# ============ 微信登录 ============

@router.post("/wechat", response_model=TokenResponse)
async def login_with_wechat(
    request: WechatLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    微信小程序登录

    1. 使用 `wx.login()` 返回的 code 调用 jscode2session
    2. 获取 openid / unionid
    3. 创建或更新用户
    4. 返回 JWT Token
    """
    # TODO: 配置微信 AppID 和 AppSecret
    wechat_app_id = getattr(settings, 'WECHAT_APP_ID', None)
    wechat_app_secret = getattr(settings, 'WECHAT_APP_SECRET', None)

    if not wechat_app_id or not wechat_app_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="微信登录未配置，请在后端 .env 文件中设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET"
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_url = "https://api.weixin.qq.com/sns/jscode2session"
            token_resp = await client.get(
                token_url,
                params={
                    "appid": wechat_app_id,
                    "secret": wechat_app_secret,
                    "js_code": request.code,
                    "grant_type": "authorization_code"
                },
                headers={
                    "User-Agent": "MakeoverCamera/1.0"
                }
            )
    except httpx.HTTPError as e:
        logger.error(f"微信 API 请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信服务暂时不可用"
        )

    if token_resp.status_code != 200:
        logger.error(
            f"微信 jscode2session HTTP 异常: status={token_resp.status_code}, body={token_resp.text[:500]}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"微信登录服务响应异常: HTTP {token_resp.status_code}"
        )

    try:
        token_data = token_resp.json()
    except ValueError:
        logger.error(f"微信返回了非 JSON 响应: {token_resp.text[:500]}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="微信登录服务返回了无效响应"
        )

    if "errcode" in token_data and token_data["errcode"] != 0:
        logger.error(f"微信登录失败: {token_data}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"微信授权失败: {token_data.get('errmsg')}"
        )

    openid = token_data["openid"]
    unionid = token_data.get("unionid")

    # 小程序登录无法直接通过 code 拿到头像昵称，后续可通过资料更新接口完善。
    nickname = "微信用户"
    avatar_url = "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0"

    user = await create_or_get_user_by_wechat(
        db, openid, unionid, nickname, avatar_url
    )

    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(str(user.id), expires_delta=access_token_expires)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600
    )


# ============ Google 登录 ============

@router.post("/google", response_model=TokenResponse)
async def login_with_google(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Google 登录

    验证 Google ID Token 并创建用户
    """
    try:
        async with httpx.AsyncClient() as client:
            # 验证 ID Token
            verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={request.id_token}"
            resp = await client.get(verify_url)

            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google ID Token"
                )

            token_info = resp.json()

            # 验证 audience（应该是你的 Google Client ID）
            # google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
            # if google_client_id and token_info.get("aud") != google_client_id:
            #     raise HTTPException(status_code=400, detail="Token audience mismatch")

            google_id = token_info.get("sub")
            email = token_info.get("email")
            nickname = token_info.get("name")
            avatar_url = token_info.get("picture")

            if not google_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token: missing user ID"
                )

            # 创建或获取用户
            user = await create_or_get_user_by_google(
                db, google_id, email, nickname, avatar_url
            )

            # 生成 JWT
            jwt_token = create_access_token(user.id)

            return TokenResponse(
                access_token=jwt_token,
                expires_in=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600
            )

    except httpx.HTTPError as e:
        logger.error(f"Google API 请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google 服务暂时不可用"
        )


# ============ 开发环境：模拟登录 ============

@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(
    nickname: str = Form(default="Test User"),
    db: AsyncSession = Depends(get_db)
):
    """
    开发环境模拟登录（仅开发环境可用）
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅开发环境可用"
        )

    import uuid
    from models.database import User
    from datetime import datetime

    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        nickname=nickname,
        preferred_language="en",
        last_login_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token(user.id)

    return TokenResponse(
        access_token=jwt_token,
        expires_in=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600
    )


# ============ 用户信息 ============

@router.get("/me", response_model=UserInfo)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserInfo(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        preferred_language=user.preferred_language,
        total_generations=user.total_generations,
        created_at=user.created_at
    )


@router.put("/me", response_model=UserInfo)
async def update_me(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户信息"""
    if request.nickname is not None:
        user.nickname = request.nickname
    if request.avatar_url is not None:
        user.avatar_url = request.avatar_url
    if request.preferred_language is not None:
        user.preferred_language = request.preferred_language
    if request.default_budget is not None:
        user.default_budget = request.default_budget

    await db.commit()
    await db.refresh(user)

    return UserInfo(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        preferred_language=user.preferred_language,
        total_generations=user.total_generations,
        created_at=user.created_at
    )


@router.post("/logout")
async def logout():
    """
    登出

    JWT 是无状态的，客户端删除 token 即可
    这里只是占位，后续可加入 token 黑名单
    """
    return {"message": "Logged out successfully"}
