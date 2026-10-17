"""
换装相机 后端主入口
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config.settings import settings, check_api_keys
from api import api_router
from models.database import init_db
from middleware.performance_logger import performance_logging_middleware

# 确保上传目录存在（在导入时就创建）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


# 创建应用
app = FastAPI(
    title="换装相机 API",
    description="AI家装轻改造助手 - 一张照片，看见家的另一种可能",
    version="0.1.0"
)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("📷 换装相机 服务启动中...")

    # 检查API密钥配置
    missing_keys = check_api_keys()
    if missing_keys:
        logger.warning(f"⚠️  以下API密钥未配置: {', '.join(missing_keys)}")
        logger.warning("部分功能将无法使用，请在 .env 文件中配置")
    else:
        logger.info("✅ 所有API密钥已配置")

    # 创建上传目录
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"📁 上传目录: {settings.UPLOAD_DIR}")

    # 初始化数据库
    await init_db()
    logger.info("📊 数据库初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("📷 换装相机 服务关闭")


# 性能监控中间件
app.middleware("http")(performance_logging_middleware)

# CORS配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js开发服务器
        "http://localhost:5173",  # Vite开发服务器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # 开发阶段允许所有来源，生产环境需要限制
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（上传的图片）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 前端静态文件目录
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

@app.get("/")
async def root():
    """根路由 - 重定向到前端页面"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/v2.zh.html")  # 默认使用中文版

# 挂载前端静态文件（放在最后，避免覆盖 API 路由）
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    logger.info(f"📂 前端目录: {FRONTEND_DIR}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
