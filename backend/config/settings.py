"""
换装相机 配置管理
所有API密钥和配置项从环境变量读取
"""
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_NAME: str = "换装相机"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "webp"}

    # 图片生成服务 - 提供商选择 (gemini | seedream)
    IMAGE_GEN_PROVIDER: str = "gemini"

    # Gemini 配置
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_URL: str = "https://xiaoai.plus/v1"
    GEMINI_MODEL: str = "gemini-3-pro-image-preview"

    # Seedream 配置（豆包/火山引擎）
    SEEDREAM_API_KEY: Optional[str] = None
    SEEDREAM_API_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    SEEDREAM_MODEL: str = "doubao-seedream-4-5-251128"

    # 兼容旧配置（已弃用，使用上面的新配置）
    IMAGE_GEN_API_KEY: Optional[str] = None
    IMAGE_GEN_API_URL: Optional[str] = "https://xiaoai.plus/v1"
    IMAGE_GEN_MODEL: str = "gemini-3-pro-image-preview"

    # VLLM 服务配置（用于物品识别和prompt生成）
    # 默认使用豆包1.8（不think模式，速度快）
    # VLLM_PROVIDER: ark（豆包 Responses API）| stepfun（OpenAI 兼容，支持 Step Plan 通道的 step-5-preview）
    VLLM_PROVIDER: str = "ark"
    VLLM_API_KEY: Optional[str] = None
    VLLM_API_URL: Optional[str] = "https://ark.cn-beijing.volces.com/api/v3"
    VLLM_MODEL: str = "doubao-seed-1-8-251228"

    # 淘宝客配置
    TAOBAO_APP_KEY: Optional[str] = None
    TAOBAO_APP_SECRET: Optional[str] = None
    TAOBAO_ADZONE_ID: Optional[str] = None

    # 大淘客配置（备选方案，接入更简单）
    DATAOKE_APP_KEY: Optional[str] = None
    DATAOKE_APP_SECRET: Optional[str] = None

    # 拼多多多多进宝配置
    PDD_CLIENT_ID: Optional[str] = None
    PDD_CLIENT_SECRET: Optional[str] = None
    PDD_PID: Optional[str] = None
    
    # 微信小程序配置
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_APP_SECRET: Optional[str] = None

    # ============================================================
    # 国际市场配置（已归档到 _archive_international/）
    # ============================================================
    # 如需恢复请参考：_archive_international/CLEANUP_NOTES.md

    # Amazon Product Advertising API (for international)
    # AMAZON_ACCESS_KEY: Optional[str] = None
    # AMAZON_SECRET_KEY: Optional[str] = None
    # AMAZON_PARTNER_TAG: Optional[str] = None
    # AMAZON_REGION: str = "us"

    # RapidAPI Key (alternative for Amazon search)
    # RAPIDAPI_KEY: Optional[str] = None

    # SerpAPI Key (alternative for Amazon search)
    # SERPAPI_KEY: Optional[str] = None

    # ============================================================

    # 默认语言（国内市场）
    DEFAULT_LANG: str = "zh"

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./homeglow.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()


def check_api_keys():
    """检查必要的API密钥是否已配置"""
    missing = []
    
    if not settings.IMAGE_GEN_API_KEY:
        missing.append("IMAGE_GEN_API_KEY")
    if not settings.VLLM_API_KEY:
        missing.append("VLLM_API_KEY")
    
    # 检查电商API（拼多多/淘宝客/大淘客 任一即可）
    has_pdd = settings.PDD_CLIENT_ID and settings.PDD_CLIENT_SECRET and settings.PDD_PID
    has_taobao = settings.TAOBAO_APP_KEY and settings.TAOBAO_APP_SECRET
    has_dataoke = settings.DATAOKE_APP_KEY and settings.DATAOKE_APP_SECRET
    
    if not (has_pdd or has_taobao or has_dataoke):
        missing.append("PDD 或 TAOBAO 或 DATAOKE 配置")
    
    return missing
